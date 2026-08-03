from app.services import email_service


class FakeDb:
    def __init__(self):
        self.added = []

    def add(self, item):
        self.added.append(item)

    def flush(self):
        pass


class FakeSMTP:
    calls = []

    def __init__(self, host, port, timeout, context=None):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.context = context
        self.started_tls = False
        FakeSMTP.calls.append(("connect", host, port, timeout, bool(context)))

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None

    def starttls(self, context=None):
        self.started_tls = True
        FakeSMTP.calls.append(("starttls", bool(context)))

    def login(self, user, password):
        FakeSMTP.calls.append(("login", user, password))

    def send_message(self, _message):
        FakeSMTP.calls.append(("send_message", self.started_tls))


def configure_email(monkeypatch, port):
    monkeypatch.setattr(email_service.settings, "EMAIL_ENABLED", True)
    monkeypatch.setattr(email_service.settings, "SMTP_HOST", "mail.talentsag.ma")
    monkeypatch.setattr(email_service.settings, "SMTP_PORT", port)
    monkeypatch.setattr(email_service.settings, "SMTP_USER", "user@talentsag.ma")
    monkeypatch.setattr(email_service.settings, "SMTP_PASSWORD", "secret")
    monkeypatch.setattr(email_service.settings, "SMTP_FROM_EMAIL", "user@talentsag.ma")
    monkeypatch.setattr(email_service.settings, "SMTP_TIMEOUT_SECONDS", 30)


def test_port_465_uses_smtp_ssl(monkeypatch):
    configure_email(monkeypatch, 465)
    FakeSMTP.calls = []
    monkeypatch.setattr(email_service.smtplib, "SMTP_SSL", FakeSMTP)
    monkeypatch.setattr(
        email_service.smtplib,
        "SMTP",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(AssertionError("SMTP should not be used for port 465")),
    )

    log = email_service.send_candidate_email(
        FakeDb(),
        to_email="candidate@example.com",
        subject="Test",
        body="Bonjour",
    )

    assert log.status == "sent"
    assert ("connect", "mail.talentsag.ma", 465, 30, True) in FakeSMTP.calls
    assert ("send_message", False) in FakeSMTP.calls
    assert ("starttls", True) not in FakeSMTP.calls


def test_port_587_uses_starttls(monkeypatch):
    configure_email(monkeypatch, 587)
    FakeSMTP.calls = []
    monkeypatch.setattr(email_service.smtplib, "SMTP", FakeSMTP)

    log = email_service.send_candidate_email(
        FakeDb(),
        to_email="candidate@example.com",
        subject="Test",
        body="Bonjour",
    )

    assert log.status == "sent"
    assert ("connect", "mail.talentsag.ma", 587, 30, False) in FakeSMTP.calls
    assert ("starttls", True) in FakeSMTP.calls
    assert ("send_message", True) in FakeSMTP.calls
