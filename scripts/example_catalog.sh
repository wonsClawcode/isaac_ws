#!/usr/bin/env bash

isaaclab_default_example() {
  local mode="${1:-gui}"
  case "${mode}" in
    gui)
      printf '%s\n' "scripts/tutorials/00_sim/spawn_prims.py"
      ;;
    headless)
      printf '%s\n' "scripts/tutorials/00_sim/create_empty.py"
      ;;
    *)
      return 1
      ;;
  esac
}

resolve_isaaclab_example() {
  local value="${1:-}"
  local mode="${2:-gui}"
  if [[ -z "${value}" ]]; then
    isaaclab_default_example "${mode}"
    return 0
  fi

  case "${value}" in
    empty|create_empty|scripts/tutorials/00_sim/create_empty.py)
      printf '%s\n' "scripts/tutorials/00_sim/create_empty.py"
      ;;
    spawn_prims|prims|scripts/tutorials/00_sim/spawn_prims.py)
      printf '%s\n' "scripts/tutorials/00_sim/spawn_prims.py"
      ;;
    *)
      printf '%s\n' "${value}"
      ;;
  esac
}

isaaclab_example_alias() {
  local script_path="$1"
  case "${script_path}" in
    scripts/tutorials/00_sim/create_empty.py)
      printf '%s\n' "empty"
      ;;
    scripts/tutorials/00_sim/spawn_prims.py)
      printf '%s\n' "spawn_prims"
      ;;
    *)
      printf '%s\n' "custom"
      ;;
  esac
}

isaaclab_example_summary() {
  local script_path="$1"
  case "${script_path}" in
    scripts/tutorials/00_sim/create_empty.py)
      printf '%s\n' "빈 stage만 초기화한다. GUI가 떠도 거의 아무 동작이 없어 보일 수 있다."
      ;;
    scripts/tutorials/00_sim/spawn_prims.py)
      printf '%s\n' "ground plane과 기본 prim을 스폰한다. GUI에서는 빈 장면보다 오브젝트가 분명하게 보여야 한다."
      ;;
    *)
      printf '%s\n' "사용자 지정 Isaac Lab tutorial script를 실행한다."
      ;;
  esac
}

isaacsim_default_example() {
  printf '%s\n' "standalone_examples/api/isaacsim.simulation_app/hello_world.py"
}

resolve_isaacsim_example() {
  local value="${1:-}"
  if [[ -z "${value}" ]]; then
    isaacsim_default_example
    return 0
  fi

  case "${value}" in
    hello_world|standalone_examples/api/isaacsim.simulation_app/hello_world.py)
      printf '%s\n' "standalone_examples/api/isaacsim.simulation_app/hello_world.py"
      ;;
    *)
      printf '%s\n' "${value}"
      ;;
  esac
}

isaacsim_example_alias() {
  local example_path="$1"
  case "${example_path}" in
    standalone_examples/api/isaacsim.simulation_app/hello_world.py)
      printf '%s\n' "hello_world"
      ;;
    *)
      printf '%s\n' "custom"
      ;;
  esac
}

isaacsim_example_summary() {
  local example_path="$1"
  case "${example_path}" in
    standalone_examples/api/isaacsim.simulation_app/hello_world.py)
      printf '%s\n' "Isaac Sim standalone hello-world app를 연다. GUI smoke와 base runtime 확인에 적합하다."
      ;;
    *)
      printf '%s\n' "사용자 지정 Isaac Sim standalone example을 실행한다."
      ;;
  esac
}

print_examples_catalog() {
  cat <<'EOF'
Isaac Lab examples
  spawn_prims
    path: scripts/tutorials/00_sim/spawn_prims.py
    default mode: gui
    expected: ground plane과 prim이 stage에 나타난다.

  empty
    path: scripts/tutorials/00_sim/create_empty.py
    default mode: headless
    expected: 빈 stage만 뜬다. 오류가 아니어도 GUI가 심심하게 보일 수 있다.

Isaac Sim examples
  hello_world
    path: standalone_examples/api/isaacsim.simulation_app/hello_world.py
    default mode: gui
    expected: Isaac Sim standalone app가 떠서 base runtime을 확인할 수 있다.
EOF
}
