{ nixpkgs, pynix, python_pkgs }:
let
  commit = "46b5dda05a90bec77d78ba93f360767d8d0b552c"; # v8.1.1
  sha256 = "0778i56k97kj1iw93gn9rihgac3mbhibjz0a6l78k4dnhggaap3v";
  bundle = let
    src = builtins.fetchTarball {
      inherit sha256;
      url =
        "https://gitlab.com/dmurciaatfluid/redshift_client/-/archive/${commit}/redshift_client-${commit}.tar";
    };
  in import "${src}/build" {
    inherit src;
    inherit nixpkgs pynix;
  };
in bundle.builders.pkgBuilder (bundle.builders.requirements python_pkgs)
