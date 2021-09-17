# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 20:23:12 2021

@author: Kareem Felfel
"""
import requests
import json
from datetime import date, timedelta, datetime
from fpdf import FPDF
import calendar
import matplotlib.pyplot as plt
from os.path import isfile
import os

def getExpectedSchedule(holidays, data, schedule):
    sDateHolder = [int(i) for i in data["startDate"].split('-')]
    eDateHolder = [int(i) for i in data["endDate"].split('-')]
    #sdateholder has 3 elements first is year, second is month, and third is day
    startDate = date(sDateHolder[0], sDateHolder[1], sDateHolder[2])
    endDate = date(eDateHolder[0], eDateHolder[1], eDateHolder[2])
    
    
    #This array holds an array of all mondays in first element, all Tuesdays in second element, etc
    allDates = getDateArray(startDate, endDate, holidays)
    expectedSchedule = {
            "students":[]
    }
    for student in schedule["students"]:
        obj = {
                "email": student["email"],
                "name" : student["name"],
                "schedule": generateStudentSchedule(student["schedule"], allDates)
        }
        expectedSchedule["students"].append(obj)
        
    return expectedSchedule
    
def generateStudentSchedule(schedule, allDates):
    returnedSchedule = []
    for item in schedule:
        day = item["day"]
        start = datetime.strptime(item["start"], "%I:%M %p")
        end = datetime.strptime(item["end"], "%I:%M %p")
        startTime = datetime.strftime(start, "%H:%M:%S")
        endTime = datetime.strftime(end, "%H:%M:%S")
        for d in allDates[day]:
            obj = {
                    "start": str(d.year) + '-' + d.strftime('%m') + '-' + d.strftime('%d') + 'T' + str(startTime),
                    "end": str(d.year) + '-' + d.strftime('%m') + '-' + d.strftime('%d') + 'T' + str(endTime)
            }
            returnedSchedule.append(obj)
            
    return returnedSchedule
        

def getDateArray(startDate, endDate, holidays):
    arr = []
    for i in range(0,7):
        arr.append(getAllDates(i, startDate, endDate, holidays))
    return arr
    
def testDates(day, sDate, eDate, holidays):
    for d in getAllDates(day, sDate, eDate, holidays):
        print ("%s, %d/%d/%d" % (calendar.day_name[d.weekday()], d.year, d.month, d.day))
  
    
def getAllDates(day, startDate, endDate, holidays):
    dateArray = []
    #first desired day of week:
    date = startDate + timedelta(days=(day - startDate.weekday() + 7) % 7) 
    while date <= endDate:
        if(isHoliday(date, holidays) is False):
            dateArray.append(date)
        date += timedelta(days = 7)
    return dateArray
                
def isHoliday(pDate, holidays):
    for hDate in holidays["holidays"]:
            From = [int(i) for i in hDate["from"].split('-')]
            dateFrom = date(From[0], From[1], From[2])
            To = [int(i) for i in hDate["to"].split('-')]
            dateTo = date(To[0], To[1], To[2])
            if(pDate >= dateFrom and pDate <= dateTo):
                return True
    return False
    
        
def main():
    print("loading local data...")
    #data has key, startDate, and endDate
    data = getData()
    holidays = getHolidays()
    #Change the days from weekdays to numbers: Monday = 0, Sunday = 6
    schedule = updateDays(getSchedule()) 
    print("Connecting to Clockify server...")
    response = getResponse(data)
    expectedSchedule = getExpectedSchedule(holidays, data, schedule)
    print("Analyzing data...")
    reports = analyzeData(response, expectedSchedule, data["timeMarginOfError"])
    for obj in reports:
        if len(obj["report"]) > 0:
            for report in obj["report"]:
                print(report)
    export = input("Would you like to have the PDF report exported to reports directory? (y/n)")
    if export.lower() == "y":
        #The name of the PDF file that will be saved
        fileName = 'report-from ' + data["startDate"] + ' to ' + data["endDate"]
        exportReport(reports, fileName, data)
    else:
        exit()
    
def exportReport(reports, fileName, data):  
    path = 'Reports/' + fileName + '.pdf'
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font('Times', '', 9)
    pdf.cell(1,1, 'From ' + data["startDate"] + ' to ' + data["endDate"] )
    pdf.ln(5)
    pdf.set_font('Times', 'B', 14)
    # Header title
    title = 'Reports For Lab & FSR Students'
    # Calculate width of title and position
    w = pdf.get_string_width(title) + 6
    pdf.set_x((210 - w) / 2)
    # Colors of frame, background and text
    pdf.set_draw_color(0, 80, 180)
    pdf.set_fill_color(250, 250, 250)
    pdf.set_text_color(220, 50, 50)
    # Thickness of frame (1 mm)
    pdf.set_line_width(1)
    # Title
    pdf.cell(w, 9, title, 1, 1, 'C', 1)
    # Line break
    pdf.ln(20)
    
    #Body for first student report:
    pdf.set_text_color(0, 0, 0)
    for student in reports:
        pdf.set_font('Times', 'B', 12)
        pdf.cell(40, 10, student["name"] + " (" + student["email"] + "):")
        # Line break
        pdf.ln(10)
        
        #plot image
        labels = 'Shifts Made on Time', 'Shifts Missed', 'Shifts Started Late', 'Shifts Left Early'
        sizes = [student["shiftsOnTime"], student["shiftsMissed"], student["shiftsStartedLate"], student["shiftsLeftEarly"]]
        colors = ['#00b300','#df4759', '#ffc107', '#FFA500']
        explode = (0, 0, 0, 0)  # only "explode" the 1st slice (i.e. 'shifts on time')
        

        fig1, ax1 = plt.subplots()
        ax1.pie(sizes, colors = colors, explode=explode, autopct=lambda p: '{:.1f}% ({:.0f})'.format(p,(p/100)*student["totalShifts"]),
        shadow=True, startangle=90)
        plt.legend(labels = labels)
        
        centre_circle = plt.Circle((0,0),0.70,fc='white')
        fig = plt.gcf()
        fig.gca().add_artist(centre_circle)
        
        ax1.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
        plt.tight_layout()
        #name of the plot image
        filePath = 'Assets/Charts/' + student["email"] + '-' + str(datetime.today().strftime('%Y-%m-%d')) + '.png'
        plt.savefig(filePath)
        
        
        #wait for it to finish
        while True:
            if isfile( filePath ): # Check if file exists
                break
        #time.sleep(5)
        #Grab the saved image and add it to the pdf
        pdf.cell(40)
        pdf.image(filePath, w= 95, h=65)
        
        #Body
        pdf.set_font('Times', '', 12)
        for data in student["report"]:
            pdf.ln(10)
            pdf.cell(5)
            pdf.cell(5, 5, '- ' + data)
    
        
        #remove the created file
        os.remove(filePath)
        # Line break
        pdf.ln(15)
    
    
    #pdf.cell(60)
    # pdf.cell(40, 10, 'Reports For Lab & FSR Students')
    pdf.output(path, 'F')
    return

def updateDays(schedule):
     #keep these as English reference to week days
    week_days=["monday","tuesday","wednesday","thursday","friday","saturday","sunday"]
    for student in schedule["students"]:
        for entry in student["schedule"]:
            if entry["day"].lower() in week_days:
                entry["day"] = week_days.index(entry["day"].lower()) #Change the day from weekday to index
            else:
                raise Exception("Please make sure that days in the schedule are spelled correctly.")
    return schedule
                
def analyzeData(response, schedule, marginOfError):
    reports = []
    responseData = response["timeentries"]
    studentsList = schedule["students"]
    for student in studentsList:
        email = student["email"]
        name = student["name"]
        shiftsMissed = 0
        shiftsLeftEarly = 0
        shiftsStartedLate = 0
        totalShifts = 0
        studentReport = []
        for entry in student["schedule"]:
            totalShifts += 1
            expectedStartDate = datetime.strptime(entry["start"], "%Y-%m-%dT%H:%M:%S")
            expectedEndDate = datetime.strptime(entry["end"], "%Y-%m-%dT%H:%M:%S")
            
            for i, item in enumerate(responseData):
                if(item["userEmail"].lower() == email.lower()):
                    startDate = datetime.strptime(item["timeInterval"]["start"].replace("-04:00", ""), "%Y-%m-%dT%H:%M:%S")
                    endDate = datetime.strptime(item["timeInterval"]["end"].replace("-04:00", ""), "%Y-%m-%dT%H:%M:%S")
                    #If start date and expected start date are the same
                    if startDate.date() == expectedStartDate.date():
                        # If the expected Clock in and expected Clock out is between the clocked in and clocked out period --> Break
                        # this means that the shift started either on or before the expected start date and ended either on or before
                        # the expected end date.
                        if expectedStartDate >= startDate:
                            # If the shift was done on time, or after it was supposed to be done, or less than the margin of error in minutes,
                            # Count it as a shift that is made on time
                            if expectedEndDate <= endDate or (expectedStartDate <= endDate and ((expectedEndDate - endDate).seconds / 60) < marginOfError):
                                break
                            # If this is the right shift (meaning the expectedStartDate must be less than or equal to endDate) since
                            # we already assumed that it is okay to start the shift early, but if it did start early we must make sure that
                            # it is the right shift and not a previous shift
                            elif expectedStartDate <= endDate and ((expectedEndDate - endDate).seconds / 60) >= marginOfError:
                                shiftsLeftEarly +=1
                                studentReport.append(name + ": This shift on " + str(expectedStartDate.ctime()) + " was left " + str(round((expectedEndDate - endDate).seconds / 60, 3)) + " minutes early")
                                break
                        #Check if shift is at most started 30 mins after it is supposed to
                        # if the shift started 30 mins or more after it was supposed to, keep looking for that shift
                        # if the shift is not found, then the shift was not made
                        # NOTE THAT 30 MINUTES IS THE MAXIMUM TIME GAP BETWEEN 2 SHIFTS.
                        if ((startDate - expectedStartDate).seconds / 60) <= 30:
                            if ((expectedStartDate < startDate) and (startDate - expectedStartDate).seconds / 60) >= marginOfError: # if came later than margin of error in minutes or more late
                                shiftsStartedLate += 1
                                studentReport.append(name + ": This shift on " + str(expectedStartDate.ctime()) + " was started " + str(round((startDate - expectedStartDate).seconds / 60, 3)) + " minutes late")
                            if ((expectedEndDate > endDate) and (expectedEndDate - endDate).seconds / 60) >= marginOfError: # if left 5 minutes or more early
                                shiftsLeftEarly += 1
                                studentReport.append(name + ": This shift on " + str(expectedStartDate.ctime()) + " was left " + str(round((expectedEndDate - endDate).seconds / 60, 3)) + " minutes early")
                            break
                            

                if i == len(responseData) -1:
                    shiftsMissed +=1
                    studentReport.append(name + ": This shift on " + str(expectedStartDate.ctime()) + " was not made.") 
                    
        #Put everything together in one object and push that object to the reports array
        obj = {
                "name": name,
                "email": email,
                "shiftsOnTime": totalShifts - (shiftsMissed + shiftsLeftEarly + shiftsStartedLate),
                "shiftsMissed": shiftsMissed,
                "shiftsLeftEarly": shiftsLeftEarly,
                "shiftsStartedLate": shiftsStartedLate,
                "totalShifts": totalShifts,
                "report" : studentReport
        }
        reports.append(obj)
                
    return reports

def getData():
    dataFile = open("data.json",)
    jsonFile = json.load(dataFile)
    dataFile.close
    return jsonFile

def getHolidays():
    holidaysFile = open("holidays.json",)
    jsonFile = json.load(holidaysFile)
    holidaysFile.close
    return jsonFile

def getSchedule():
    scheduleFile = open("schedule.json",)
    jsonFile = json.load(scheduleFile)
    scheduleFile.close
    return jsonFile

def getResponse(data):
    header = {
            'content-type': 'application/json',
            'X-Api-Key': data['key']
    }
    # ISO format
    startDate = data['startDate'] + 'T00:00:00.000'
    endDate = data['endDate'] + 'T23:59:59.000'
    request = json.dumps({
            "dateRangeStart": startDate,
            "dateRangeEnd": endDate,
            "detailedFilter": {
                    "page": 1,
                    "pageSize": 1000,
                    "sortColumn": "DATE"
            },
            "sortOrder": "ASCENDING"
            })
    id = data["workspaceID"]
    URL = 'https://reports.api.clockify.me/v1/workspaces/'+ id + '/reports/detailed'
    try:
        response = requests.post(URL, headers = header, data = request)
        return response.json()
    except:
        raise Exception("Failed to connect to Clockify Server.")
main()