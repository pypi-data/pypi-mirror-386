from datetime import datetime, timezone

now = datetime.now(timezone.utc)
iso_str = f"{now.strftime('%Y-%m-%dT%H:%M:%S')}.{now.microsecond:06d}000Z"
print(iso_str)