import datetime

import markdown2
import os
import psutil
from dotenv import load_dotenv
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from sqlalchemy.ext.asyncio import AsyncSession
from reporting.models import ServerReporting
from url_scheduler.models import PingResponse
from .models import JsonReporting
from sqlalchemy.future import select

from .ai_externe import gpt_call
from .oyen import ask_report_to_oyen
load_dotenv()

async def enhancement_data_stats_average(database: AsyncSession):

    hours = int(os.environ.get("REPORTING_PINGS_TIMELAPS",12))
    now = datetime.datetime.now(datetime.timezone.utc)
    since = now - datetime.timedelta(hours=hours)

    result = await database.execute(select(PingResponse).filter(PingResponse.created_at >= since))
    pings_model = result.scalars().all()

    if not pings_model:
        return {"message": "No data"}

    times = [ping.response.get("response_time_ms", 0) for ping in pings_model]
    codes = [ping.response.get("status_code", 0) for ping in pings_model]

    return {
        "total_pings": len(pings_model),
        "avg_response_time_ms": round(sum(times) / len(times), 2),
        "min_response_time_ms": min(times),
        "max_response_time_ms": max(times),
        "status_codes_distribution": {code: codes.count(code) for code in set(codes)},
    }

async def enhancement_server_stats(database: AsyncSession):

        cpu_percent = psutil.cpu_percent(interval=1)

        ram = psutil.virtual_memory()
        ram_total = round(ram.total / (1024 ** 3), 2)  # en Go
        ram_used = round(ram.used / (1024 ** 3), 2)
        ram_percent = ram.percent

        disk = psutil.disk_usage('/')
        disk_total = round(disk.total / (1024 ** 3), 2)
        disk_used = round(disk.used / (1024 ** 3), 2)
        disk_percent = disk.percent

        net = psutil.net_io_counters()
        bytes_sent = round(net.bytes_sent / (1024 ** 2), 2)  # en Mo
        bytes_recv = round(net.bytes_recv / (1024 ** 2), 2)

        result = {
            "cpu_percent": cpu_percent,
            "ram": {
                "total_gb": ram_total,
                "used_gb": ram_used,
                "percent": ram_percent,
            },
            "disk": {
                "total_gb": disk_total,
                "used_gb": disk_used,
                "percent": disk_percent,
            },
            "network": {
                "sent_mb": bytes_sent,
                "recv_mb": bytes_recv,
            }
        }

        server_reporting_model = ServerReporting(
            response=result
        )

        database.add(server_reporting_model)
        await database.commit()
        await database.refresh(server_reporting_model)

        return result

async def enhancement_reporting_server_average(database: AsyncSession):

        timelaps = int(os.environ.get("REPORTING_PINGS_TIMELAPS",43200))
        now = datetime.datetime.now(datetime.timezone.utc)
        since = now - datetime.timedelta(hours=timelaps)

        result = await database.execute(select(ServerReporting).filter(ServerReporting.created_at >= since))

        server_model = result.scalars().all()

        if not server_model:
            return {"message": "No data"}

        cpu_percent = [server.response.get("cpu_percent") for server in server_model if
                       server.response.get("cpu_percent") is not None]
        ram_used = [server.response.get("ram", {}).get("used_gb") for server in server_model if
                    server.response.get("ram", {}).get("used_gb") is not None]
        ram_percent = [server.response.get("ram", {}).get("percent") for server in server_model if
                       server.response.get("ram", {}).get("percent") is not None]
        disk_used = [server.response.get("disk", {}).get("used_gb") for server in server_model if
                     server.response.get("disk", {}).get("used_gb") is not None]
        disk_percent = [server.response.get("disk", {}).get("percent") for server in server_model if
                        server.response.get("disk", {}).get("percent") is not None]
        net_sent = [server.response.get("network", {}).get("sent_mb") for server in server_model if
                    server.response.get("network", {}).get("sent_mb") is not None]
        net_recv = [server.response.get("network", {}).get("recv_mb") for server in server_model if
                    server.response.get("network", {}).get("recv_mb") is not None]

        def avg(data):
            return round(sum(data) / len(data), 2) if data else 0

        return {
            "cpu_percent": avg(cpu_percent),
            "ram_used_gb": avg(ram_used),
            "ram_percent": avg(ram_percent),
            "disk_used_gb": avg(disk_used),
            "disk_percent": avg(disk_percent),
            "network": {
                "sent_mb": avg(net_sent),
                "recv_mb": avg(net_recv),
            }
        }

async def oyen_reporting_average(database: AsyncSession):
    # Récupération sécurisée des données
    try:
        server_data = await enhancement_reporting_server_average(database)
        pings_data = await enhancement_data_stats_average(database)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"error": "Failed to fetch performance data"}

    formatted_data = {
        "server_metrics": {
            "cpu_percent": server_data.get('cpu_percent', 0),
            "ram_used_gb": server_data.get('ram_used_gb', 0),
            "ram_percent": server_data.get('ram_percent', 0),
            "disk_used_gb": server_data.get('disk_used_gb', 0),
            "disk_percent": server_data.get('disk_percent', 0),
            "network": {
                "sent_mb": server_data.get('network', {}).get('sent_mb', 0),
                "recv_mb": server_data.get('network', {}).get('recv_mb', 0)
            }
        },
        "url_inspections": {
            "total_pings": pings_data.get('total_pings', 0),
            "avg_response_time_ms": pings_data.get('avg_response_time_ms', 0),
            "min_response_time_ms": pings_data.get('min_response_time_ms', 0),
            "max_response_time_ms": pings_data.get('max_response_time_ms', 0),
            "status_codes_distribution": pings_data.get('status_codes_distribution', {})
        }
    }

    network_total = (formatted_data['server_metrics']['network']['sent_mb'] +
                     formatted_data['server_metrics']['network']['recv_mb'])
    total_pings = formatted_data['url_inspections']['total_pings']
    redirects = formatted_data['url_inspections']['status_codes_distribution'].get('307', 0)
    redirect_ratio = (redirects / total_pings) * 100 if total_pings > 0 else 0

    prompt = f"""
    Generate a COMPLETE technical report in French following EXACTLY this Markdown structure.
    
    INSTRUCTIONS:
    1. Output must contain ALL sections with exactly the structure shown above
    2. Replace ALL placeholders with actual values
    3. Use proper Markdown formatting including code blocks
    4. Maintain consistent number formatting (decimal places)
    5. Include the complete JSON data block as shown
    6. Do not add any additional text outside the markdown code block
    
    Replace all placeholders with actual values and maintain perfect formatting:
    
    ```markdown
    # System Performance Analysis Report
    
    ## Summary
    1. Server resource utilization overview:
       - CPU: {formatted_data['server_metrics']['cpu_percent']}%
       - RAM: {formatted_data['server_metrics']['ram_percent']}% ({formatted_data['server_metrics']['ram_used_gb']}GB used)
       - Disk: {formatted_data['server_metrics']['disk_percent']}% ({formatted_data['server_metrics']['disk_used_gb']}GB used)
    
    2. URL performance metrics:
       - Total pings: {formatted_data['url_inspections']['total_pings']}
       - Average response time: {formatted_data['url_inspections']['avg_response_time_ms']}ms
       - Response time range: {formatted_data['url_inspections']['min_response_time_ms']}ms - {formatted_data['url_inspections']['max_response_time_ms']}ms
    
    3. Key observations:
       - CPU usage at {formatted_data['server_metrics']['cpu_percent']}% indicates available capacity
       - High average response time ({formatted_data['url_inspections']['avg_response_time_ms']}ms) exceeds typical targets
       - Network traffic is balanced ({network_total:.2f}MB total transfer)
    
    ## Analysis
    1. Performance Assessment:
       - Server resources appear underutilized (CPU: {formatted_data['server_metrics']['cpu_percent']}%)
       - Response time variation suggests potential bottlenecks
       - Memory usage ({formatted_data['server_metrics']['ram_percent']}%) is within normal range
    
    2. Reliability Indicators:
       - Disk has ample capacity remaining ({formatted_data['server_metrics']['disk_percent']}% used)
       - Network traffic is balanced ({network_total:.2f}MB total)
       - Status code distribution: 200={formatted_data['url_inspections']['status_codes_distribution'].get('200', 0)}, 307={formatted_data['url_inspections']['status_codes_distribution'].get('307', 0)}
    
    3. Technical Findings:
       - Response time spikes (max: {formatted_data['url_inspections']['max_response_time_ms']}ms) need investigation
       - {redirect_ratio:.1f}% of requests are 307 redirects which may impact performance
       - No critical resource shortages detected
    
    ## Improvement Recommendations
    1. Immediate Actions:
       - [ ] Investigate high average response time ({formatted_data['url_inspections']['avg_response_time_ms']}ms)
       - [ ] Analyze endpoints causing max response time ({formatted_data['url_inspections']['max_response_time_ms']}ms)
       - [ ] Review necessity of {redirects} 307 redirects ({redirect_ratio:.1f}% of requests)
    
    2. Medium-term Improvements:
       - [ ] Implement response time monitoring with alerts >1000ms
       - [ ] Optimize backend services contributing to latency
       - [ ] Consider caching for frequently accessed URLs
    
    3. Monitoring Suggestions:
       - [ ] Track response time percentiles over time
       - [ ] Monitor CPU utilization during peak periods
       - [ ] Watch disk usage growth trends
    """

    try:
        result = await ask_report_to_oyen(prompt)

        clean_result = clean_markdown_output(result)

        result_pdf = markdown_to_pdf_no_pandoc(clean_result,"system_report.pdf")

        return result
    except Exception as e:
        print(f"Error generating report: {e}")
        return "Failed to generate report due to internal error"


async def gpt_reporting_average(database: AsyncSession):
    try:
        server_data = await enhancement_reporting_server_average(database)
        pings_data = await enhancement_data_stats_average(database)
    except Exception as e:
        print(f"Error fetching data: {e}")
        return {"error": "Failed to fetch performance data"}

    formatted_data = {
        "server_metrics": {
            "cpu_percent": server_data.get('cpu_percent', 0),
            "ram_used_gb": server_data.get('ram_used_gb', 0),
            "ram_percent": server_data.get('ram_percent', 0),
            "disk_used_gb": server_data.get('disk_used_gb', 0),
            "disk_percent": server_data.get('disk_percent', 0),
            "network": {
                "sent_mb": server_data.get('network', {}).get('sent_mb', 0),
                "recv_mb": server_data.get('network', {}).get('recv_mb', 0)
            }
        },
        "url_inspections": {
            "total_pings": pings_data.get('total_pings', 0),
            "avg_response_time_ms": pings_data.get('avg_response_time_ms', 0),
            "min_response_time_ms": pings_data.get('min_response_time_ms', 0),
            "max_response_time_ms": pings_data.get('max_response_time_ms', 0),
            "status_codes_distribution": pings_data.get('status_codes_distribution', {})
        }
    }

    # Calculs préliminaires
    network_total = (formatted_data['server_metrics']['network']['sent_mb'] +
                     formatted_data['server_metrics']['network']['recv_mb'])
    total_pings = formatted_data['url_inspections']['total_pings']
    redirects = formatted_data['url_inspections']['status_codes_distribution'].get('307', 0)
    redirect_ratio = (redirects / total_pings) * 100 if total_pings > 0 else 0

    # Template complet avec toutes les sections
    prompt = f"""
    Generate a COMPLETE technical report in French following EXACTLY this Markdown structure.

    INSTRUCTIONS:
    1. Output must contain ALL sections with exactly the structure shown above
    2. Replace ALL placeholders with actual values
    3. Use proper Markdown formatting including code blocks
    4. Maintain consistent number formatting (decimal places)
    6. Do not add any additional text outside the markdown code block
    7. The reporting need absolutly to be in french

    Replace all placeholders with actual values and maintain perfect formatting:

    ```markdown
    # System Performance Analysis Report

    ## Summary
    1. Server resource utilization overview:
       - CPU: {formatted_data['server_metrics']['cpu_percent']}%
       - RAM: {formatted_data['server_metrics']['ram_percent']}% ({formatted_data['server_metrics']['ram_used_gb']}GB used)
       - Disk: {formatted_data['server_metrics']['disk_percent']}% ({formatted_data['server_metrics']['disk_used_gb']}GB used)

    2. URL performance metrics:
       - Total pings: {formatted_data['url_inspections']['total_pings']}
       - Average response time: {formatted_data['url_inspections']['avg_response_time_ms']}ms
       - Response time range: {formatted_data['url_inspections']['min_response_time_ms']}ms - {formatted_data['url_inspections']['max_response_time_ms']}ms

    3. Key observations:
       - CPU usage at {formatted_data['server_metrics']['cpu_percent']}% indicates available capacity
       - High average response time ({formatted_data['url_inspections']['avg_response_time_ms']}ms) exceeds typical targets
       - Network traffic is balanced ({network_total:.2f}MB total transfer)

    ## Analysis
    1. Performance Assessment:
       - Server resources appear underutilized (CPU: {formatted_data['server_metrics']['cpu_percent']}%)
       - Response time variation suggests potential bottlenecks
       - Memory usage ({formatted_data['server_metrics']['ram_percent']}%) is within normal range

    2. Reliability Indicators:
       - Disk has ample capacity remaining ({formatted_data['server_metrics']['disk_percent']}% used)
       - Network traffic is balanced ({network_total:.2f}MB total)
       - Status code distribution: 200={formatted_data['url_inspections']['status_codes_distribution'].get('200', 0)}, 307={formatted_data['url_inspections']['status_codes_distribution'].get('307', 0)}

    3. Technical Findings:
       - Response time spikes (max: {formatted_data['url_inspections']['max_response_time_ms']}ms) need investigation
       - {redirect_ratio:.1f}% of requests are 307 redirects which may impact performance
       - No critical resource shortages detected

    ## Improvement Recommendations
    1. Immediate Actions:
       - [ ] Investigate high average response time ({formatted_data['url_inspections']['avg_response_time_ms']}ms)
       - [ ] Analyze endpoints causing max response time ({formatted_data['url_inspections']['max_response_time_ms']}ms)
       - [ ] Review necessity of {redirects} 307 redirects ({redirect_ratio:.1f}% of requests)

    2. Medium-term Improvements:
       - [ ] Implement response time monitoring with alerts >1000ms
       - [ ] Optimize backend services contributing to latency
       - [ ] Consider caching for frequently accessed URLs

    3. Monitoring Suggestions:
       - [ ] Track response time percentiles over time
       - [ ] Monitor CPU utilization during peak periods
       - [ ] Watch disk usage growth trends
    """

    # Génération du rapport avec gestion des erreurs
    try:
        result = await gpt_call(prompt)

        clean_result = clean_markdown_output(result)

        json_model = JsonReporting(
            response=clean_result
        )

        database.add(json_model)
        await database.commit()
        await database.refresh(json_model)

        result_pdf = markdown_to_pdf_no_pandoc(clean_result,"system_report.pdf")

        return clean_result
    except Exception as e:
        print(f"Error generating report: {e}")
        return "Failed to generate report due to internal error"

def clean_markdown_output(raw_text: str) -> str:
    if raw_text.startswith("```markdown"):
        raw_text = raw_text[len("```markdown"):].strip()
    if raw_text.endswith("```"):
        raw_text = raw_text[:-3].strip()
    return raw_text


def markdown_to_pdf_no_pandoc(markdown_text: str, output_file: str = "report.pdf"):
    html = markdown2.markdown(markdown_text)

    doc = SimpleDocTemplate(output_file)
    styles = getSampleStyleSheet()
    story = []

    for line in html.splitlines():
        if line.strip():
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 12))

    doc.build(story)
    return output_file