import os
import httpx
import sentry_sdk
import posthog


def init_observability() -> None:
    sentry_dsn = os.getenv("SENTRY_DSN")
    if sentry_dsn:
        sentry_sdk.init(
            dsn=sentry_dsn,
            traces_sample_rate=float(os.getenv("SENTRY_TRACES_SAMPLE_RATE", "1.0")),
            profiles_sample_rate=float(os.getenv("SENTRY_PROFILES_SAMPLE_RATE", "0.1")),
            environment=os.getenv("PITH_ENV", "dev"),
            release=os.getenv("PITH_RELEASE", "pith@dev"),
        )

    posthog_key = os.getenv("POSTHOG_API_KEY")
    if posthog_key:
        posthog.project_api_key = posthog_key
        posthog.host = os.getenv("POSTHOG_HOST", "https://eu.i.posthog.com")


def set_scope(trace_id: str | None = None, task_id: str | None = None, user_id: str | None = None, **tags) -> None:
    with sentry_sdk.configure_scope() as scope:
        if trace_id:
            scope.set_tag("trace_id", trace_id)
        if task_id:
            scope.set_tag("task_id", task_id)
        if user_id:
            scope.set_user({"id": user_id})
        for k, v in tags.items():
            if v is not None:
                scope.set_tag(str(k), str(v))


def capture_event(user_id: str, event: str, props: dict | None = None) -> None:
    if os.getenv("POSTHOG_API_KEY"):
        posthog.capture(user_id, event, props or {})


def capture_exception(exc: Exception, extra: dict | None = None) -> None:
    if extra:
        with sentry_sdk.configure_scope() as scope:
            for k, v in extra.items():
                scope.set_extra(k, v)
    sentry_sdk.capture_exception(exc)


async def create_linear_issue(title: str, description: str):
    api_key = os.getenv("LINEAR_API_KEY")
    team_id = os.getenv("LINEAR_TEAM_ID")
    if not api_key or not team_id:
        return None

    query = """
    mutation CreateIssue($title: String!, $description: String!, $teamId: String!) {
      issueCreate(input: {title: $title, description: $description, teamId: $teamId}) {
        success
        issue { id identifier url }
      }
    }
    """

    async with httpx.AsyncClient(timeout=20) as client:
        response = await client.post(
            "https://api.linear.app/graphql",
            headers={"Authorization": api_key},
            json={
                "query": query,
                "variables": {
                    "title": title,
                    "description": description,
                    "teamId": team_id,
                },
            },
        )
        response.raise_for_status()
        data = response.json()
        return data["data"]["issueCreate"]["issue"]
