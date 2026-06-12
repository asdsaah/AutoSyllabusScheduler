import pandas as pd
import datetime
from datetime import timedelta
import xlsxwriter

# ==========================================
# IMPORT USER DATA (The "Sidecar")
# ==========================================
try:
    from my_syllabus import COLORS, syllabus_data, START_DATE, END_DATE
except ImportError:
    print("CRITICAL ERROR: Could not find 'my_syllabus.py'.")
    print("Make sure you have a file named 'my_syllabus.py' in the same folder.")
    print("This file should contain your COLORS, syllabus_data, START_DATE, and END_DATE.")
    exit()

# File Name
OUTPUT_FILENAME = f"Study_Schedule_{START_DATE.year}.xlsx"

# ==========================================
# GENERATE EXCEL (LOGIC ENGINE)
# ==========================================

def generate_schedule():
    # Create a list of all dates in the semester
    all_dates = [START_DATE + timedelta(days=x) for x in range((END_DATE - START_DATE).days + 1)]
    
    # Initialize Workbook
    workbook = xlsxwriter.Workbook(OUTPUT_FILENAME)
    worksheet = workbook.add_worksheet("Gantt Schedule")
    
    # --- FORMATTING ---
    fmt_header = workbook.add_format({'bold': True, 'bg_color': '#404040', 'font_color': 'white', 'border': 1, 'align': 'center'})
    fmt_date = workbook.add_format({'bold': True, 'bg_color': '#f0f0f0', 'border': 1, 'align': 'center', 'font_size': 9})
    fmt_weekend = workbook.add_format({'bold': True, 'bg_color': '#d9d9d9', 'border': 1, 'align': 'center', 'font_size': 9})
    
    # Pre-generate formats for each class
    class_formats = {}
    for cls, clrs in COLORS.items():
        f_light = workbook.add_format({'bg_color': clrs['hex'], 'border': 1, 'text_wrap': True, 'valign': 'top', 'font_size': 10})
        f_dark = workbook.add_format({'bg_color': clrs['dark_hex'], 'border': 1, 'text_wrap': True, 'valign': 'top', 'font_size': 10})
        f_dark_bold = workbook.add_format({'bg_color': clrs['dark_hex'], 'border': 1, 'text_wrap': True, 'valign': 'top', 'font_size': 10, 'bold': True})
        
        class_formats[cls] = {'light': f_light, 'dark': f_dark, 'dark_bold': f_dark_bold}

    # --- WRITING HEADERS ---
    
    # Extract class list from the imported COLORS dict
    # We filter out 'General' to put it at the end if desired, or just use keys
    classes = [k for k in COLORS.keys() if k != 'General']
    classes.append("Weekly Strategy")
    
    # Set Column Widths
    worksheet.set_column(0, 0, 25) # Class Name Column
    for i in range(1, len(all_dates) + 1):
        worksheet.set_column(i, i, 18) # Date Columns
        
    worksheet.write(1, 0, "Class / Date", fmt_header)
    
    # Write Dates
    date_col_map = {} 
    for idx, d in enumerate(all_dates):
        col = idx + 1
        date_col_map[d] = col
        date_str = d.strftime("%a\n%b %d")
        
        if d.weekday() >= 5:
            worksheet.write(0, col, "Weekend", fmt_weekend)
            worksheet.write(1, col, date_str, fmt_weekend)
        else:
            worksheet.write(1, col, date_str, fmt_date)

    # --- PROCESS & WRITE TASKS BY ROW ---
    
    # Organize syllabus by class
    class_syll = {c: [] for c in classes}
    for item in syllabus_data:
        # Check if class name exists in our keys (handling case mismatch safety)
        if item[0] in class_syll:
            class_syll[item[0]].append(item)
            
    for cls_idx, cls_name in enumerate(classes):
        row = cls_idx + 2
        worksheet.write(row, 0, cls_name, fmt_header)
        worksheet.set_row(row, 70)
        
        # Strategy Row Logic
        if cls_name == "Weekly Strategy":
            for d in all_dates:
                if d.weekday() == 6: # Sunday
                    col = date_col_map[d]
                    worksheet.write(row, col, "1. Look Ahead\n2. Review Notes", class_formats['General']['dark'])
            continue

        # --- BUILD ROW STATE ---
        row_plan = {}
        
        # 1. First Pass: Place "Dark" Class Events
        for _, date_str, type, task, link in class_syll[cls_name]:
            class_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            
            if class_date not in row_plan:
                row_plan[class_date] = {'type': 'dark', 'text': [], 'bold': False, 'link': None}
            
            row_plan[class_date]['text'].append(f"{type}: {task}")
            
            # Bold these types so they stand out in the Dark cells
            if type in ["Field Trip", "Exam", "Quiz", "Deadline"]:
                row_plan[class_date]['bold'] = True
                
            if link and not row_plan[class_date]['link']:
                row_plan[class_date]['link'] = link
                
        # 2. Second Pass: Place "Light" Prep Blocks
        for _, date_str, type, _, _ in class_syll[cls_name]:
            class_date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            
            # Exclude "Major" items from having prep days
            if type in ["Field Trip", "Exam", "Quiz", "Deadline"]:
                continue
                
            for offset in [1, 2, 3]:
                prep_date = class_date - timedelta(days=offset)
                
                if prep_date < START_DATE or prep_date > END_DATE:
                    continue
                    
                if prep_date in row_plan and row_plan[prep_date]['type'] == 'dark':
                    continue 
                
                row_plan[prep_date] = {'type': 'light', 'text': [], 'bold': False, 'link': None}

        # --- WRITE ROW TO EXCEL ---
        for d in all_dates:
            if d in row_plan:
                col = date_col_map[d]
                cell_data = row_plan[d]
                
                fmt = class_formats[cls_name]['dark_bold'] if cell_data['bold'] else class_formats[cls_name]['dark'] if cell_data['type'] == 'dark' else class_formats[cls_name]['light']
                display_text = "\n".join(cell_data['text']) if cell_data['type'] == 'dark' else ""
                
                if cell_data['link'] and display_text:
                    worksheet.write_url(row, col, cell_data['link'], fmt, string=display_text)
                else:
                    worksheet.write(row, col, display_text, fmt)

    worksheet.freeze_panes(2, 1)
    workbook.close()
    print(f"Schedule generated successfully: {OUTPUT_FILENAME}")

if __name__ == "__main__":
    generate_schedule()