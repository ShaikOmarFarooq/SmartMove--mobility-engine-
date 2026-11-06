import requests
import time
import json

PROJECT_KEY = "dva506-project4"
PROJECT_NAME = "DVA506 - Project 4"
SONAR_TOKEN = "squ_e40fb6f4a5083654960cc07f377a04a88649fcbc"

def create_report():
    metrics = "bugs,vulnerabilities,code_smells,coverage,duplicated_lines_density"
    url = f"http://sonarqube:9000/api/measures/component?component={PROJECT_KEY}&metricKeys={metrics}"

    try: 
        response = requests.get(url, auth=(SONAR_TOKEN, ""))
        if response.status_code == 200:
            data = response.json()

            measures = data['component']['measures']
            final_report = {
                "project": PROJECT_NAME,
                "analysis_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "results": {m['metric']: m['value'] for m in measures}
            }

            file_name = f"report_{PROJECT_KEY}.json"
            with open(file_name, "w", encoding="utf-8") as f:
                json.dump(final_report, f, indent=4)

        else:
            print(f"Fail to recover the report: {response.text}")

    except Exception as e:
        print(f"Error during the save of the report: {e}")


create_report()