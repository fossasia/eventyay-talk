FAQ
===

This document collects issues that came up in the past, and that cannot be
solved in pretalx with a reasonable amount of effort or time.

Sessions
--------

What is the difference between tracks and session types?
    Tracks are a way to group sessions by topic, and will be shown in the
    schedule as colour-coded blocks. Session types are a way to determine
    the format and default duration of a session. See more in the
    :ref:`Session user guide <user-guide-tracks>`.

What is the difference between the “accepted” and “confirmed” session status?
    The “accepted” status is used to indicate that a session has been
    accepted by the program committee. The “confirmed” status is used to
    indicate that the speaker has confirmed their participation in the
    conference. The “confirmed” status is set by the speaker, though organisers
    can also set it manually. See more in the :ref:`Session user guide <user-guide-sessions>`.

How do I designate sessions as fallback/alternates?
    To designate sessions as fallback or alternates, you can use the **pending states** feature.
    To do so, leave the session in the “submitted” state, but set it to “pending accepted”.
    Pending states are not shown to speakers, but you can write an email to all speakers with
    proposals marked as “pending accepted” if you want to communicate this decision.
    For more details on how to manage session states, see the
    :ref:`Session Lifecycle <user-guide-proposals-pending>` section in the
    :ref`Sessions & Proposals <user-guide-proposals>` guide.

Email
-----

We run into issues when using Gmail.
    In Google’s eyes, pretalx is a `less secure app`_, which you’ll have to
    grant special access. Even then, Gmail is known to unexpectedly block your
    SMTP connection with unhelpful error messages if you use it to send out too
    many emails in bulk (e.g. all rejections for a conference) even on GSuite,
    so using Gmail for transactional email is a bad idea.

.. _less secure app: https://support.google.com/accounts/answer/6010255
