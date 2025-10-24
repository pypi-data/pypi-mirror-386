import datetime
import json

from typing import TypedDict
from google.cloud import logging


class ErrorUtils(TypedDict):
    logger: logging.Logger
    env: str
    app_project_id: str
    topic_project_id: str
    topic_id: str
    app_name: str
    teams_channel: str


class DateUtils:
    @staticmethod
    def get_str_utc_timestamp():
        dt = datetime.datetime.utcnow()
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + ".000000000Z"

    @staticmethod
    def get_str_utc_timestamp_minus_5min():
        dt = datetime.datetime.utcnow() - datetime.timedelta(minutes=5)
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + ".000000000Z"

    @staticmethod
    def get_str_utc_timestamp_plus_5min():
        dt = datetime.datetime.utcnow() + datetime.timedelta(minutes=5)
        return dt.strftime("%Y-%m-%dT%H:%M:%S") + ".000000000Z"


def format_email_template(email_object, email_messages, table_data, app_name):
    html = f"""
        <html>
            <head lang="fr">
                <meta charset="utf-8">
                <meta name="x-apple-disable-message-reformatting">
                <meta name="viewport" content="width=device-width, initial-scale=1">
                <title>Contrôle datastream</title>
            </head>
            <body style="margin:0; padding:0; background:#f5f7fb;">
                <table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="background:#f5f7fb;">
                    <tr>
                        <td align="center" style="padding:24px;">
                            <table role="presentation" cellpadding="0" cellspacing="0" border="0" style="max-width:100%; background:#ffffff; border-radius:8px; border:1px solid #e6e9ef;">
                                <tr>
                                    <td style="text-align: center; padding-top: 12px;">
                                        <img style="height: 24px;" src="https://upload.wikimedia.org/wikipedia/fr/f/fd/Logo_Paris_Turf.svg" alt="" srcset="">
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding:24px 24px 12px 24px; font-family:Segoe UI, Arial, sans-serif; font-size:20px; line-height:26px; color:#111827; font-weight:700;">
                                        Objet : {email_object}
                                    </td>
                                </tr>

                                {build_html_message(email_messages)}

                                <tr>
                                    <td style="padding:0 16px 24px 16px;">
                                        {build_html_table(table_data, app_name)}
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding:0 16px 24px 16px;">
                                        {build_snippet_html_part(table_data, app_name) if table_data else ""}
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding:0 24px 16px 24px; font-family:Segoe UI, Arial, sans-serif; font-size:14px; line-height:20px; color:#4b5563;">
                                        Cordialement,
                                    </td>
                                </tr>

                                <tr>
                                    <td style="padding:0 24px 24px 24px; font-family:Segoe UI, Arial, sans-serif; font-size:12px; line-height:18px; color:#6b7280;">
                                        <div style="border-top:1px solid #eef2f7; padding-top:12px;text-align: center;">
                                        Message automatique – ne pas répondre. <br>
                                        © 2025 Paris-Turf – Tous droits réservés <br>
                                        <a href="https://www.paris-turf.com">www.paris-turf.com</a>
                                        </div>
                                    </td>
                                </tr>
                            </table>
                        </td>
                    </tr>
                </table>
            </body>
        </html>
    """
    return html


def build_html_table(table_data: list, app_name: str):
    if app_name == "health_check_check_horses_stats":
        html_table = '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse; font-family:Segoe UI, Arial, sans-serif;">'

        # format header
        html_table += "<tr>"
        for header in table_data[0]:
            html_table += f'<th style="padding:10px; font-size:14px; line-height:20px; color:#111827; border-bottom:1px solid #bbbbbb;">{header}</th>'
        html_table += "</tr>"

        # format rows
        for row in table_data[1:]:
            html_table += "<tr>"
            for cell in row:
                html_table += f'<td style="padding:10px; font-size:14px; line-height:20px; color:#111827; border-bottom:1px solid #bbbbbb;">{cell}</td>'
            html_table += "</tr>"

        html_table += "</table>"

        return html_table

    elif app_name == "health_check_check_partants_data":
        return build_html_table_partants_course(table_data)

    else:
        return ""


def build_html_table_partants_course(table_data: list):
    html_table = '<table role="presentation" cellpadding="0" cellspacing="0" border="0" width="100%" style="border-collapse:collapse; font-family:Segoe UI, Arial, sans-serif;">'

    # format header
    html_table += """
        <tr>
            <th align="center" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;" rowspan="2">ID Course</th>
            <th align="center" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;" rowspan="2">Date Course</th>
            <th align="center" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;" colspan="2">NB initial runners</th>
            <th align="center" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;" colspan="2">NB non runners</th>
            <th align="center" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;" colspan="2">Non runners</th>
            <th align="center" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;" colspan="2">NB runners</th>
        </tr>
        <tr>
            <th align="left" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;">Postgres</th>
            <th align="left" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;">Mongo</th>
            <th align="left" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;">Postgres</th>
            <th align="left" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;">Mongo</th>
            <th align="left" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;">Postgres</th>
            <th align="left" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;">Mongo</th>
            <th align="left" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;">Postgres</th>
            <th align="left" style="padding:12px 10px; font-size:12px; line-height:16px; color:#374151; text-transform:uppercase; letter-spacing:.5px; border:2px solid #e5e7eb; background:#f9fafb;">Mongo</th>
        </tr>
    """
    # format rows
    for row in table_data:
        html_table += "<tr>"
        for cell in row:
            html_table += f'<td style="padding:10px; font-size:14px; line-height:20px; color:#111827; border:1px solid #bbbbbb;">{cell}</td>'
        html_table += "</tr>"

    html_table += "</table>"

    return html_table


def build_html_message(email_messages: list[str]):
    content = ""
    for email_message in email_messages:
        content += f"""
            <tr>
                <td style="padding:0 24px 16px 24px; font-family:Segoe UI, Arial, sans-serif; font-size:14px; line-height:20px; color:#4b5563;">
                    {email_message}
                </td>
            </tr>
        """
    return content


def is_json(value):
    if not isinstance(value, str):
        return False  # ce n'est même pas une chaîne
    try:
        json.loads(value)
        return True
    except json.JSONDecodeError:
        return False


def build_snippet_html_part(table_data: list, app_name: str):
    content = ""

    if app_name == "health_check_check_horses_stats":
        content = """
            <div style="font-weight:bold;margin-bottom:6px;">Requêtes pour relancer le calcul des stats:</div>
            <div style="background:#0b1021;color:#e6e6e6;padding:12px;border-radius:4px;font-family:monospace;font-size:13px;line-height:1.5;white-space:pre;">
        """
        for row in table_data[1:]:
            content += f"<span> SELECT * FROM ps_force_relaunch_stat_cheval_apres_course('{row[0]}'); </span> <br/>"
        content += "</div>"

    elif app_name == "health_check_check_partants_data":
        nb_runners_is_different = False
        content = """
            <div style="font-weight:bold;margin-bottom:6px;">Requêtes pour relancer l'aggregation:</div>
            <div style="background:#0b1021;color:#e6e6e6;padding:12px;border-radius:4px;font-family:monospace;font-size:13px;line-height:1.5;white-space:pre;">
        """
        for row in table_data:
            content += (
                f"<span> SELECT * FROM ps_force_relaunch_transaction('tb_course','{row[0]}', false); </span> <br/>"
            )
            if row[8] != row[9]:
                nb_runners_is_different = True
        content += "</div>"

        if nb_runners_is_different:
            content += """
                <div style="font-size: 14px;color: orange;">*Les commandes ont été exécutées automatiquement afin de corriger l’écart du nombre de runners. </div>
            """

    elif app_name in (
        "health_check_check_processing_queue_ids_avant_course",
        "health_check_check_processing_queue_ids_apres_course",
    ):
        content = """
            <div style="font-weight:bold;margin-bottom:6px;">Requêtes pour ajouter les ids dans la file d'attente de stats_processing_queue:</div>
            <div style="background:#0b1021;color:#e6e6e6;padding:12px;border-radius:4px;font-family:monospace;font-size:13px;line-height:1.5;white-space:pre;">
        """
        for row in table_data:
            content += f"<span> INSERT INTO tb_stats_processing_queue (id, person_type, table_name, ref_race_id) VALUES ({row[0]}, '{row[1]}', '{row[2]}', {row[3]}) ON CONFLICT (status, id, person_type, table_name, ref_race_id) DO NOTHING;; </span> <br/>"
        content += "</div>"

    return content
