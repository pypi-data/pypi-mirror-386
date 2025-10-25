{ nixpkgs, python_pkgs }:
python_pkgs.snowflake-connector-python.overridePythonAttrs (old: {
  version = "3.14.0";
  src = nixpkgs.fetchFromGitHub {
    owner = "snowflakedb";
    repo = "snowflake-connector-python";
    tag = "v3.14.0";
    hash = "sha256-r3g+eVVyK9t5qpAGvimapuWilAh3eHJEFUw8VBwtKw8=";
  };
  disabledTestPaths = old.disabledTestPaths
    ++ [ "test/unit/test_wiremock_client.py" "test/unit/test_put_get.py" ];
})
