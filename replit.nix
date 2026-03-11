{ pkgs }: {
  deps = [
    pkgs.python311
    pkgs.python311Packages.pip
    pkgs.postgresql   # provides pg_config needed to compile psycopg2
    pkgs.gcc
    pkgs.libffi
    pkgs.zlib
    pkgs.openssl
  ];
}
