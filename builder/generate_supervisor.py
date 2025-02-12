import argparse
from pathlib import Path


def generate_supervisor_config(workdir: Path):
    invokeai_path = workdir / "invokeai"
    app_path = workdir / "app"
    builder_path = workdir / "builder"
    template_path = builder_path / "supervisor.temp.conf"
    output_path = Path("/etc/supervisor/conf.d/supervisor.conf")

    # Read template file
    with open(template_path, "r") as template_file:
        template = template_file.read()

    # Replace placeholders
    config = template.replace("{{INVOKEAI_PATH}}", invokeai_path.as_posix()).replace("{{APP_PATH}}", app_path.as_posix())

    # Write final supervisor config
    with open(output_path, "w") as config_file:
        config_file.write(config)

    print(f"Supervisor config generated successfully at {output_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--workdir", required=True)

    args = parser.parse_args()
    generate_supervisor_config(Path(args.workdir).resolve())
