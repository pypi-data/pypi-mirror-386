{ nixpkgs, pynix, }:
let
  layer_1 = python_pkgs:
    python_pkgs // {
      arch-lint = import ./arch_lint.nix { inherit nixpkgs pynix python_pkgs; };
    };
  layer_2 = python_pkgs:
    python_pkgs // {
      fa-purity = import ./fa_purity.nix { inherit nixpkgs pynix python_pkgs; };
    };
  layer_3 = python_pkgs:
    python_pkgs // {
      redshift-client =
        import ./redshift_client.nix { inherit nixpkgs pynix python_pkgs; };
      snowflake-connector-python = import ./snowflake_connector_python.nix {
        inherit nixpkgs python_pkgs;
      };
    };
  python_pkgs =
    pynix.utils.compose [ layer_3 layer_2 layer_1 ] pynix.lib.pythonPackages;
in { inherit python_pkgs; }
