"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

from datetime import datetime
from protocol_interfaces import EventProtocolInterface
from models import ReliabilityTests, database
from logutils import get_logger

logger = get_logger(__name__)


class ReliabilityEventAdapter(EventProtocolInterface):
    """Adapter for integrating Reliability's Event protocol."""

    def create(self, **kwargs):
        pass

    def read(self, resource_id, **kwargs):
        pass

    def update(self, resource_id, **kwargs):
        sms_sent_timestamp = kwargs["sms_sent_timestamp"]
        sms_received_timestamp = kwargs["sms_received_timestamp"]

        if not sms_sent_timestamp:
            error_message = "sms_sent_timestamp is required."
            logger.error(error_message)
            return {
                "success": False,
                "message": error_message,
            }
        if not sms_received_timestamp:
            error_message = "sms_received_timestamp is required."
            logger.error(error_message)
            return {
                "success": False,
                "message": error_message,
            }

        try:
            with database.atomic():
                test_record = ReliabilityTests.get(ReliabilityTests.id == resource_id)

                if test_record.status in ["success", "timedout"]:
                    logger.info(
                        "Test ID %d is already marked as '%s'. Ignoring update.",
                        resource_id,
                        test_record.status,
                    )
                    return {
                        "success": False,
                        "message": f"Test ID {resource_id} is already "
                        f"marked as '{test_record.status}'.",
                    }
                test_record.sms_sent_time = datetime.fromtimestamp(
                    int(sms_sent_timestamp)
                )
                test_record.sms_received_time = datetime.fromtimestamp(
                    int(sms_received_timestamp)
                )
                test_record.sms_routed_time = datetime.now()
                test_record.status = "success"
                test_record.save()

                logger.info(
                    "Test ID %d updated successfully with status 'success'.",
                    resource_id,
                )

                return {
                    "success": True,
                    "message": f"Test ID {resource_id} updated successfully.",
                }

        except ReliabilityTests.DoesNotExist:
            error_message = f"Test ID {resource_id} not found in the database."
            logger.error(error_message)
            return {
                "success": False,
                "message": error_message,
            }

    def delete(self, resource_id, **kwargs):
        pass
