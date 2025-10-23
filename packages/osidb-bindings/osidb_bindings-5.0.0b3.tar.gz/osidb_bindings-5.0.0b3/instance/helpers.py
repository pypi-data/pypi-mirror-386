flaw_data = {
    "title": "skynet walks the earth",
    "components": ["sky", "net"],
    "impact": "MODERATE",
    "source": "INTERNET",
    "reported_dt": "2025-01-01",
    "unembargo_dt": "2025-01-01",
    "embargoed": False,
    "comment_zero": "skynet is everywhere",
    "owner": "jfrejlac",
    "cve_id": "CVE-2025-1001",
}


def create_new_flaw(cve_id=""):
    flaw_data = {
        "title": "skynet walks the earth",
        "components": ["sky", "net"],
        "impact": "MODERATE",
        "source": "INTERNET",
        "reported_dt": "2025-01-01",
        "unembargo_dt": "2025-01-01",
        "embargoed": False,
        "comment_zero": "skynet is everywhere",
        "owner": "jfrejlac",
        "cve_id": cve_id,
    }


import osidb_bindings


class DataCreator:
    def __init__(self, env="local", session=None):
        if session is not None:
            self.session = session
        else:
            if env == "local":
                self.session = osidb_bindings.new_session(
                    osidb_server_uri="http://localhost:8000",
                    username="testuser",
                    password="password",
                )

    def create_new_flaw(self, cve_id=""):
        flaw_data = {
            "title": "skynet walks the earth",
            "components": ["sky", "net"],
            "impact": "MODERATE",
            "source": "INTERNET",
            "reported_dt": "2025-01-01",
            "unembargo_dt": "2025-01-01",
            "embargoed": False,
            "comment_zero": "skynet is everywhere",
            "owner": "jfrejlac",
            "cve_id": cve_id,
        }

        try:
            r = self.session.flaws.create(form_data=flaw_data)
        except Exception as e:
            print(e.response.content)
            raise e

        flaw = self.session.flaws.retrieve(r.uuid)

        affect_data = {
            "flaw": str(flaw.uuid),
            "affectedness": "AFFECTED",
            "resolution": "DELEGATED",
            "embargoed": flaw.embargoed,
            "ps_update_stream": "rhel-9.8",
            "ps_component": "kernel-rt",
        }

        try:
            self.session.affects.create(form_data=affect_data)
        except Exception as e:
            print(e.response.content)
            raise e

        if cve_id:
            print(f"Flaw with CVE '{cve_id}' created.")
        else:
            print(f"Flaw with UUID '{r.uuid}' created.")
