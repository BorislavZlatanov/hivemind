#! /bin/bash

set -e

SCRIPTSDIR="$(dirname "$(realpath "$0")")/.."

export LOG_FILE=build_instance.log
# shellcheck source=../haf/scripts/common.sh
source "$SCRIPTSDIR/../haf/scripts/common.sh"

BUILD_IMAGE_TAG=""
REGISTRY=""
SRCROOTDIR=""

print_help () {
cat <<EOF
Usage: $0 <image_tag> <src_dir> <registry_url> [OPTION[=VALUE]]...
Allows to build docker image containing Hivemind installation
The image will be tagged with name '<registry_url>/instance:instance-<image_tag>'

OPTIONS:
  -?,--help                        Display this help screen and exit
  --dot-env-filename=<filename> File name of the dot env file to be generated
  --dot-env-var-name=<var name> Vaiable name to be used in the generated file (default: 'IMAGE')
EOF
}

while [ $# -gt 0 ]; do
  case "$1" in
    -?|--help)
        print_help
        exit 0
        ;;
    --dot-env-filename=*)
        DOT_ENV_FILENAME="${1#*=}"
        ;;
    --dot-env-var-name=*)
        DOTENV_VAR_NAME="${1#*=}"
        ;;
    *)
        if [ -z "$BUILD_IMAGE_TAG" ];
        then
          BUILD_IMAGE_TAG="${1}"
        elif [ -z "$SRCROOTDIR" ];
        then
          SRCROOTDIR="${1}"
        elif [ -z "$REGISTRY" ];
        then
          REGISTRY=${1}
        else
          echo "ERROR: '$1' is not a valid option/positional argument"
          echo
          print_help
          exit 1
        fi
        ;;
    esac
    shift
done

[[ -z "$BUILD_IMAGE_TAG" ]] && printf "Missing argument #1 - image tag suffix\n\n" && print_help && exit 1
[[ -z "$SRCROOTDIR" ]] && printf "Missing argument #2 - source directory path\n\n" && print_help && exit 1
[[ -z "$REGISTRY" ]] && printf "Missing argument #3 - target container registry URL\n\n" && print_help && exit 1

printf "Moving into source root directory: %s\n" "$SRCROOTDIR"

pushd "$SRCROOTDIR"
pwd

"$SRCROOTDIR/scripts/ci/fix_ci_tag.sh"

BUILD_OPTIONS=("--platform=amd64" "--target=instance" "--progress=plain")
TAG="$REGISTRY/instance:instance-$BUILD_IMAGE_TAG"

docker buildx build "${BUILD_OPTIONS[@]}" \
  --build-arg CI_REGISTRY_IMAGE="$REGISTRY/" \
  --tag "$TAG" \
  --file Dockerfile .

[[ -n "${DOT_ENV_FILENAME:-}" ]] && echo "${DOTENV_VAR_NAME:-IMAGE}=$TAG" > "$DOT_ENV_FILENAME"

popd