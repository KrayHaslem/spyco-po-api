"""
SMS service for sending text messages via ClickSend API.
"""

import os
import base64
import logging
import requests

logger = logging.getLogger(__name__)

# ClickSend API configuration
CLICKSEND_API_URL = "https://rest.clicksend.com/v3/sms/send"
SMS_COMPANY_SUFFIX = " -Sent by Spyco Oilfield Service"


def _get_config():
    """Get configuration from environment (called at runtime, not import time)."""
    return {
        "username": os.environ.get("CLICKSEND_USERNAME"),
        "api_key": os.environ.get("CLICKSEND_API_KEY"),
        "client_url": os.environ.get("CLIENT_URL", "http://localhost:5173"),
    }


def _get_auth_header() -> dict:
    """
    Generate the Basic Auth header for ClickSend API.
    
    Returns:
        Dict with Authorization header
    """
    config = _get_config()
    if not config["username"] or not config["api_key"]:
        logger.error("ClickSend credentials not configured")
        return {}
    
    credentials = f"{config['username']}:{config['api_key']}"
    encoded = base64.b64encode(credentials.encode()).decode()
    return {"Authorization": f"Basic {encoded}"}


def send_sms(to: str, message: str) -> bool:
    """
    Send a single SMS message.
    
    Args:
        to: Phone number to send to (10-digit US format)
        message: Message body to send
        
    Returns:
        True if message was queued successfully, False otherwise
    """
    config = _get_config()
    
    if not config["username"] or not config["api_key"]:
        logger.error("ClickSend credentials not configured")
        return False
    
    try:
        headers = {
            **_get_auth_header(),
            "Content-Type": "application/json"
        }
        
        payload = {
            "messages": [
                {
                    "to": to,
                    "body": message + SMS_COMPANY_SUFFIX,
                    "source": "spyco-po",
                    "country": "US"
                }
            ]
        }
        
        response = requests.post(
            CLICKSEND_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("response_code") == "SUCCESS":
                # Check individual message status
                sms_messages = data.get("data", {}).get("messages", [])
                if sms_messages:
                    msg = sms_messages[0]
                    msg_status = msg.get("status")
                    if msg_status == "SUCCESS":
                        return True
                    else:
                        return False
                return True
            else:
                return False
        else:
            logger.error(f"HTTP {response.status_code} - {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("Request timed out")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"Request failed - {str(e)}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error - {str(e)}")
        return False


def send_bulk_sms(recipients: list[dict]) -> dict:
    """
    Send SMS messages to multiple recipients.
    
    Args:
        recipients: List of dicts with 'to' and 'message' keys
                   Example: [{'to': '5551234567', 'message': 'Hello'}]
        
    Returns:
        Dict with 'success_count', 'failure_count', and 'results' list
    """
    config = _get_config()
    
    results = {
        "success_count": 0,
        "failure_count": 0,
        "results": []
    }
    
    if not recipients:
        return results
    
    if not config["username"] or not config["api_key"]:
        logger.error("ClickSend credentials not configured")
        results["failure_count"] = len(recipients)
        return results
    
    try:
        headers = {
            **_get_auth_header(),
            "Content-Type": "application/json"
        }
        
        messages = []
        for recipient in recipients:
            if recipient.get("to") and recipient.get("message"):
                messages.append({
                    "to": recipient["to"],
                    "body": recipient["message"] + SMS_COMPANY_SUFFIX,
                    "source": "spyco-po",
                    "country": "US"
                })
        
        if not messages:
            return results
        
        payload = {"messages": messages}
        
        response = requests.post(
            CLICKSEND_API_URL,
            json=payload,
            headers=headers,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("response_code") == "SUCCESS":
                queued = data.get("data", {}).get("queued_count", 0)
                results["success_count"] = queued
                results["failure_count"] = len(messages) - queued
            else:
                results["failure_count"] = len(messages)
        else:
            results["failure_count"] = len(messages)
            logger.error(f"Bulk HTTP {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        results["failure_count"] = len(recipients)
        logger.error("Bulk request timed out")
    except requests.exceptions.RequestException as e:
        results["failure_count"] = len(recipients)
        logger.error(f"Bulk request failed - {str(e)}")
    except Exception as e:
        results["failure_count"] = len(recipients)
        logger.error(f"Bulk unexpected error - {str(e)}")
    
    return results


# ============== Notification Helper Functions ==============

def notify_order_pending(order, approvers: list, submitter_name: str):
    """
    Notify approvers that a new order is pending approval.
    
    Args:
        order: The Order object
        approvers: List of Approver objects
        submitter_name: Name of the user who submitted the order
    """
    config = _get_config()
    
    recipients = []
    for approver in approvers:
        if approver.user and approver.user.phone:
            phone = approver.user.phone
            message = (
                f"New order {order.order_number} pending approval from {submitter_name}. "
                f"{config['client_url']}/orders/{order.id}"
            )
            recipients.append({
                "to": phone,
                "message": message
            })
    
    if recipients:
        send_bulk_sms(recipients)


def notify_repair_pending(repair, approvers: list, submitter_name: str):
    """
    Notify approvers that a new repair is pending approval.
    
    Args:
        repair: The Repair object
        approvers: List of Approver objects
        submitter_name: Name of the user who submitted the repair
    """
    config = _get_config()
    
    recipients = []
    for approver in approvers:
        if approver.user and approver.user.phone:
            message = (
                f"New repair {repair.repair_number} pending approval from {submitter_name}. "
                f"{config['client_url']}/repairs/{repair.id}"
            )
            recipients.append({
                "to": approver.user.phone,
                "message": message
            })
    
    if recipients:
        send_bulk_sms(recipients)


def notify_order_approved(order, admins: list):
    """
    Notify admins that an order has been approved.
    
    Args:
        order: The Order object
        admins: List of User objects (admins)
    """
    config = _get_config()
    
    recipients = []
    for admin in admins:
        if admin.phone:
            message = (
                f"Order {order.order_number} has been approved. "
                f"{config['client_url']}/orders/{order.id}"
            )
            recipients.append({
                "to": admin.phone,
                "message": message
            })
    
    if recipients:
        send_bulk_sms(recipients)


def notify_repair_approved(repair, technicians: list):
    """
    Notify technicians that a repair has been approved and is ready for completion.
    
    Args:
        repair: The Repair object
        technicians: List of Technician objects
    """
    config = _get_config()
    
    recipients = []
    for technician in technicians:
        if technician.user and technician.user.phone:
            message = (
                f"Repair {repair.repair_number} approved and ready for completion. "
                f"{config['client_url']}/repairs/{repair.id}"
            )
            recipients.append({
                "to": technician.user.phone,
                "message": message
            })
    
    if recipients:
        send_bulk_sms(recipients)


def notify_order_paid(order, user):
    """
    Notify the original order creator that their order has been paid.
    
    Args:
        order: The Order object
        user: The User who created the order
    """
    config = _get_config()
    
    if not user or not user.phone:
        return
    
    vendor_name = order.vendor.name if order.vendor else "Unknown Vendor"
    po_number = order.po_group.po_number if order.po_group else "N/A"
    
    message = (
        f"Your order from {vendor_name} has been paid. "
        f"PO#: {po_number}. "
        f"{config['client_url']}/orders/{order.id}"
    )
    
    send_sms(user.phone, message)


def notify_repair_completed(repair, user):
    """
    Notify the original repair requester that their repair has been completed.
    
    Args:
        repair: The Repair object
        user: The User who requested the repair
    """
    config = _get_config()
    
    if not user or not user.phone:
        return
    
    message = (
        f"Your repair {repair.repair_number} has been marked complete. "
        f"{config['client_url']}/repairs/{repair.id}"
    )
    
    send_sms(user.phone, message)
