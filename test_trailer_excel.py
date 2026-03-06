import requests
import io


def main():
    login_data = {
        "username": "skara",
        "password": "!23efe25ali!",
        "grant_type": "password",
    }
    print("Testing Login...")
    res_login = requests.post(
        "http://127.0.0.1:8080/api/v1/auth/token", data=login_data
    )
    if res_login.status_code != 200:
        print("Login failed")
        return

    token = res_login.json().get("access_token")
    headers = {
        "Authorization": f"Bearer {token}",
    }

    print("\nTesting GET /api/v1/trailers/export")
    res_export = requests.get(
        "http://127.0.0.1:8080/api/v1/trailers/export", headers=headers
    )
    print("Export Status:", res_export.status_code)
    if res_export.status_code == 200:
        print(f"Export successful. Downloaded {len(res_export.content)} bytes.")
        with open("exported_trailers.xlsx", "wb") as f:
            f.write(res_export.content)
    else:
        print("Export failed:", res_export.text)

    print("\nTesting GET /api/v1/trailers/template")
    res_template = requests.get(
        "http://127.0.0.1:8080/api/v1/trailers/template", headers=headers
    )
    print("Template Status:", res_template.status_code)
    if res_template.status_code == 200:
        print(f"Template successful. Downloaded {len(res_template.content)} bytes.")
    else:
        print("Template failed:", res_template.text)

    print("\nTesting POST /api/v1/trailers/import")
    if res_export.status_code == 200:
        files = {
            "file": (
                "exported_trailers.xlsx",
                res_export.content,
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        }
        res_import = requests.post(
            "http://127.0.0.1:8080/api/v1/trailers/import", headers=headers, files=files
        )
        print("Import Status:", res_import.status_code)
        try:
            print("Import Response:", res_import.json())
        except:
            print("Import Response Text:", res_import.text)


if __name__ == "__main__":
    main()
