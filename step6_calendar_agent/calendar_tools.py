import sys
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from googleapiclient.errors import HttpError

from calendar_auth import get_calendar_service

TZ = "Asia/Kolkata"
_service = None


def _svc():
    global _service
    if _service is None:
        _service = get_calendar_service()
    return _service


def _confirm(prompt):
    try:
        import termios
        termios.tcflush(sys.stdin, termios.TCIFLUSH)  # drop stray pasted newlines
    except Exception:
        pass
    return input(f"{prompt} [y/N]: ").strip().lower() == "y"


def _parse(dt_str):
    """Parse an ISO datetime; treat naive values as Asia/Kolkata."""
    dt = datetime.fromisoformat(dt_str)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=ZoneInfo(TZ))
    return dt


def list_events(start, end):
    try:
        s, e = _parse(start), _parse(end)
        if e <= s:
            return {"success": False, "detail": "end must be after start"}
        result = _svc().events().list(
            calendarId="primary",
            timeMin=s.isoformat(),
            timeMax=e.isoformat(),
            singleEvents=True,
            orderBy="startTime",
            maxResults=25,
        ).execute()
        events = [
            {
                "id": ev["id"],
                "title": ev.get("summary", "(no title)"),
                "start": ev["start"].get("dateTime", ev["start"].get("date")),
                "end": ev["end"].get("dateTime", ev["end"].get("date")),
            }
            for ev in result.get("items", [])
        ]
        return {"success": True, "count": len(events), "events": events}
    except ValueError as err:
        return {"success": False, "detail": f"bad datetime: {err}"}
    except HttpError as err:
        return {"success": False, "detail": f"Google API error: {err}"}


def check_availability(start, end):
    try:
        s, e = _parse(start), _parse(end)
        if e <= s:
            return {"success": False, "detail": "end must be after start"}
        result = _svc().events().list(
            calendarId="primary",
            timeMin=s.isoformat(),
            timeMax=e.isoformat(),
            singleEvents=True,
            orderBy="startTime",
        ).execute()
        busy = [
            {
                "title": ev.get("summary", "(no title)"),
                "start": ev["start"].get("dateTime", ev["start"].get("date")),
                "end": ev["end"].get("dateTime", ev["end"].get("date")),
            }
            for ev in result.get("items", [])
            if ev.get("transparency") != "transparent"
        ]
        return {"success": True, "free": len(busy) == 0, "busy_slots": busy}
    except ValueError as err:
        return {"success": False, "detail": f"bad datetime: {err}"}
    except HttpError as err:
        return {"success": False, "detail": f"Google API error: {err}"}


def create_event(title, start, end):
    try:
        s, e = _parse(start), _parse(end)
    except ValueError as err:
        return {"success": False, "detail": f"bad datetime: {err}"}
    if e <= s:
        return {"success": False, "detail": "end must be after start"}
    if s < datetime.now(ZoneInfo(TZ)) - timedelta(minutes=1):
        return {"success": False, "detail": "start time is in the past"}

    if not _confirm(f"Create event '{title}' from {s:%a %d %b %H:%M} to {e:%H:%M}?"):
        return {
            "success": False,
            "detail": "User declined. Do not retry the same event; ask what to change.",
        }
    try:
        ev = _svc().events().insert(
            calendarId="primary",
            body={
                "summary": title,
                "start": {"dateTime": s.isoformat(), "timeZone": TZ},
                "end": {"dateTime": e.isoformat(), "timeZone": TZ},
            },
        ).execute()
        return {"success": True, "id": ev["id"], "link": ev.get("htmlLink"), "detail": "created"}
    except HttpError as err:
        return {"success": False, "detail": f"Google API error: {err}"}


def delete_event(event_id):
    try:
        ev = _svc().events().get(calendarId="primary", eventId=event_id).execute()
    except HttpError as err:
        return {"success": False, "detail": f"could not find event: {err}"}

    title = ev.get("summary", "(no title)")
    when = ev["start"].get("dateTime", ev["start"].get("date"))
    if not _confirm(f"DELETE event '{title}' ({when})?"):
        return {
            "success": False,
            "detail": "User declined. Do not retry; ask what to do differently.",
        }
    try:
        _svc().events().delete(calendarId="primary", eventId=event_id).execute()
        return {"success": True, "detail": f"deleted '{title}'"}
    except HttpError as err:
        return {"success": False, "detail": f"Google API error: {err}"}
