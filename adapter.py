"""
This program is free software: you can redistribute it under the terms
of the GNU General Public License, v. 3.0. If a copy of the GNU General
Public License was not distributed with this file, see <https://www.gnu.org/licenses/>.
"""

from datetime import datetime, timedelta
from protocol_interfaces import EventProtocolInterface
from models import GatewayClients, ReliabilityTests, database
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
            self._timeout_tests()

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
                    int(sms_sent_timestamp) / 1000
                )
                test_record.sms_received_time = datetime.fromtimestamp(
                    int(sms_received_timestamp) / 1000
                )
                test_record.sms_routed_time = datetime.now()
                test_record.status = "success"
                test_record.save()

                logger.info(
                    "Test ID %d updated successfully with status 'success'.",
                    resource_id,
                )
                reliability_score = self._calculate_reliability_score_for_client(
                    test_record.msisdn
                )

                GatewayClients.update(reliability=reliability_score).where(
                    GatewayClients.msisdn == test_record.msisdn
                ).execute()

                logger.info(
                    "Reliability score for MSISDN %s updated to %.2f%%.",
                    test_record.msisdn,
                    reliability_score,
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

    def _calculate_reliability_score_for_client(
        self, msisdn: str, threshold: int = 5
    ) -> float:
        """
        Calculate the reliability score for a gateway client based on successful SMS routing.

        Args:
            msisdn (str): The MSISDN of the client.

        Returns:
            float: Reliability percentage rounded to two decimal places.

        Notes:
            This function calculates the reliability score for a given client based on the
            percentage of successful SMS routings within a 3-minute window. Reliability is
            defined as the ratio of successful SMS routings to the total number of tests
            conducted for the client.

            A successful SMS routing is defined as a routing with a 'success' status, where
            the SMS is routed within 180 seconds (3 minutes) of being received by the system.
        """
        total_tests = (
            ReliabilityTests.select().where(ReliabilityTests.msisdn == msisdn).count()
        )

        if total_tests < threshold:
            logger.info(
                "Not enough tests for MSISDN %s to calculate reliability. "
                "Total tests: %d, Threshold: %d",
                msisdn,
                total_tests,
                threshold,
            )
            return round(0.0, 2)

        successful_tests = (
            ReliabilityTests.select()
            .where(
                ReliabilityTests.msisdn == msisdn,
                ReliabilityTests.status == "success",
                (~ReliabilityTests.sms_routed_time.is_null()),
                (
                    (
                        ReliabilityTests.sms_routed_time.to_timestamp()
                        - ReliabilityTests.sms_received_time.to_timestamp()
                    )
                    <= 300
                ),
            )
            .count()
        )

        reliability = (successful_tests / total_tests) * 100

        return round(reliability, 2)

    def _timeout_tests(self):
        """
        Update the status of tests to 'timedout' if they are older than 10 minutes.
        """
        expiration_time = datetime.now() - timedelta(minutes=10)

        timedout_tests_query = ReliabilityTests.update(status="timedout").where(
            ReliabilityTests.start_time < expiration_time,
            ReliabilityTests.status.not_in(["timedout", "success"]),
        )

        updated_count = timedout_tests_query.execute()

        if updated_count > 0:
            logger.info(
                "%d tests marked as 'timedout' due to expiration.",
                updated_count,
            )
