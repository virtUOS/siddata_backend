from backend.models import AdminReport, ReportMessage


def add_report_message(message='', title=''):
    r = AdminReport.get_pending_report()
    m = ReportMessage(title='<h2>'+title+'</h2>', message=message, report=r)
    m.save()
