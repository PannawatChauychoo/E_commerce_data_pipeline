#!/usr/bin/env bash
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

if [[ "$PWD" != "$PROJECT_DIR" ]]; then
	echo "⚠️  Please run this script from its own directory: $PROJECT_DIR"
	echo "    You’re in: $PWD"
	exit 1
fi

print_help() {
	cat <<EOF
Options:
  -h, --help    Show help
  -t, --test    Remove all test files
  -p, --prod    Remove all production files
  -a, --all     Remove all files
  --            Pass remaining args to airflow CLI
EOF
}

remove_prod() {
	rm -rf ../data_source/agm_agent_save ../data_source/agm_output/
	rm -f ./helper/id_seeds.json
}

remove_test() {
	rm -rf ../data_source/agm_agent_save_test ../data_source/agm_output_test/
	rm -f ./helper/id_seeds_test.json
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	-h | --help)
		print_help
		exit 0
		;;
	-t | --test)
		remove_test
		exit 0
		;;
	-p | --prod)
		remove_prod
		exit 0
		;;
	-a | --all)
		echo "⚠️  This will delete ALL test and production files. Are you sure? (y/N)"
		read -r confirm
		if [[ "$confirm" =~ ^[Yy]$ ]]; then
			remove_prod
			remove_test
			echo "All simulation files remove"
		else
			echo "Aborted"
		fi
		exit 0
		;;
	esac
done
