from datetime import date, timedelta
from django.utils.dateparse import parse_date


def get_date_range(request):
    
    # Parse ?start=YYYY-MM-DD&end=YYYY-MM-DD from query params.
    # Defaults to the last 30 days when not provided.
   
    today = date.today()
    default_start = today - timedelta(days=30)

    raw_start = request.query_params.get('start')
    raw_end = request.query_params.get('end')

    start_date = parse_date(raw_start) if raw_start else default_start
    end_date = parse_date(raw_end) if raw_end else today

    # Guard against reversed ranges
    if start_date > end_date:
        start_date, end_date = end_date, start_date

    return start_date, end_date