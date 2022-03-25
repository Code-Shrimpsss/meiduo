from django.core.mail import send_mail

from celery_tasks.main import celery_app


@celery_app.task(name='send_email_active')
def send_email_active(email_addr, message):
    subject = '美多购物邮箱激活'
    message = message
    from_email = '美多商城官方<wws2461692314@126.com>'
    recipient_list = [email_addr]
    send_mail(subject=subject, message='', from_email=from_email, recipient_list=recipient_list, html_message=message)
