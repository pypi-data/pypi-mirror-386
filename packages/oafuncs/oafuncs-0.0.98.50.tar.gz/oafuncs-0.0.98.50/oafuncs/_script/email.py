from rich import print

__all__ = ["send"]


def _send_message(title, content, msg_to, msg_from, password):
    from email.header import Header
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    import smtplib
    # 1. 连接邮箱服务器
    con = smtplib.SMTP_SSL("smtp.qq.com", 465)

    # 2. 登录邮箱
    # msg_from, password = _email_info()
    # con.login(msg_from, _decode_password(password))
    con.login(msg_from, password)

    # 3. 准备数据
    # 创建邮件对象
    msg = MIMEMultipart()

    # 设置邮件主题
    subject = Header(title, "utf-8").encode()
    msg["Subject"] = subject

    # 设置邮件发送者
    msg["From"] = msg_from

    # 设置邮件接受者
    msg["To"] = msg_to

    # # 添加html内容
    # content = """
    # <h2>我是正文中的标题</h2>
    # <p>邮件正文描述性文字1</p>
    # <p>邮件正文描述性文字2</p>
    # <img src='https://www.baidu.com/img/bd_logo1.png'>
    # <center>百度图片</center>
    # <a href='https://www.baidu.com'>百度一下</a>
    # """
    # html = MIMEText(content, 'html', 'utf-8')
    # msg.attach(html)

    # or
    # content = '发送内容'
    msg.attach(MIMEText(content, "plain", "utf-8"))

    # 4.发送邮件
    con.sendmail(msg_from, msg_to, msg.as_string())
    con.quit()

    print(f"已通过{msg_from}成功向{msg_to}发送邮件！")
    print("发送内容为：\n{}\n\n".format(content))


def send(title="Title", content=None, send_to: str = "email@qq.com", msg_from='must@qq.com', password='email_not_qq_pwd'):
    """
    Description: 发送邮件

    Args:
        title: 邮件标题
        content: 邮件内容
        send_to: 发送对象

    Returns:
        None

    Example:
        send(title='Title', content='Content', '123@qq.com')
    """
    if content is None or send_to=='email@qq.com' or msg_from=='must@qq.com' or password=='email_not_qq_pwd':
        return
    else:
        _send_message(title, content, send_to, msg_from, password)


if __name__ == "__main__":
    send()
