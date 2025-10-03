## Show this help message
help() {
    # Couleurs
    RED='\033[31m'
    GREEN='\033[32m'
    YELLOW='\033[33m'
    CYAN='\033[36m'
    WHITE='\033[37m'
    RESET='\033[0m'
    echo -e "${CYAN}Usage() {$0 [command]${RESET}"
    echo ""
    echo -e "${CYAN}Commands:${RESET}"
    awk '/^##/ {
        desc = substr($0, 4);
        getline;
        if ($0 ~ /\(\)/) {
            method = $1;
            gsub("\\(\\)", "", method);
            printf "  '$YELLOW'\033[33m%-20s'$RESET' %s\n", method, desc;
        }
    }' "$0"
}
# Main
if [[ $# -lt 1 ]]; then
    help
else
    "$@"
fi
