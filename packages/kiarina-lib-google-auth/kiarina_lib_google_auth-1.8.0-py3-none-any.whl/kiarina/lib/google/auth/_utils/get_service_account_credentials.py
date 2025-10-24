import os

from google.oauth2.service_account import Credentials


def get_service_account_credentials(
    *,
    service_account_file: str | os.PathLike[str] | None = None,
    service_account_data: dict[str, object] | None = None,
) -> Credentials:
    if service_account_data:
        return Credentials.from_service_account_info(service_account_data)  # type: ignore[no-untyped-call, no-any-return]

    elif service_account_file:
        service_account_file = os.path.expanduser(
            os.path.expandvars(os.fspath(service_account_file))
        )

        if not os.path.exists(service_account_file):
            raise ValueError(
                f"Service account file does not exist: {service_account_file}"
            )

        return Credentials.from_service_account_file(service_account_file)  # type: ignore[no-untyped-call, no-any-return]

    else:
        raise ValueError("No valid service account credentials found.")
