import pytest

if __name__ == "__main__":
    args = [
        # "--verbose",
        # "--html=report.html",
        "fixer",
        "--alluredir=.\\allure_rep"
    ]
    print(pytest.ExitCode(pytest.main(args)))
    args = [
        # "--verbose",
        # "--html=report.html",
        "go_mail",
        "--alluredir=.\\allure_rep"
    ]
    print(pytest.ExitCode(pytest.main(args)))
