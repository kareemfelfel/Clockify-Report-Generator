# -*- coding: utf-8 -*-
"""
Created on Mon Aug 23 20:23:12 2021

@author: Kareem Felfel
"""
import requests
import json
from datetime import date, timedelta, datetime
import calendar

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
    reports = analyzeData(response, expectedSchedule)
    if len(reports) > 0:
        for report in reports:
            print(report)
    else:
        print("All time entries are verified for FSR and LAB workers.")
    
    
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
                
def analyzeData(response, schedule):
    reports = []
    responseData = response["timeentries"]
    studentsList = schedule["students"]
    for student in studentsList:
        email = student["email"]
        name = student["name"]
        for entry in student["schedule"]:
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
                            if expectedEndDate <= endDate:
                                break
                            # If this is the right shift (meaning the expectedStartDate must be less than or equal to endDate) since
                            # we already assumed that it is okay to start the shift early, but if it did start early we must make sure that
                            # it is the right shift and not a previous shift
                            elif expectedStartDate <= endDate and ((expectedEndDate - endDate).seconds / 60) > 5:
                                reports.append(name + ": This shift on " + str(expectedStartDate.ctime()) + " was left " + str((expectedEndDate - endDate).seconds / 60) + " minutes early")
                                break
                        #Check if shift is at most started 30 mins after it is supposed to
                        # if the shift started 30 mins or more after it was supposed to, keep looking for that shift
                        # if the shift is not found, then the shift was not made
                        if ((startDate - expectedStartDate).seconds / 60) <= 30:
                            if ((expectedStartDate < startDate) and (startDate - expectedStartDate).seconds / 60) > 5: # if came 5 minutes or more late
                                reports.append(name + ": This shift on " + str(expectedStartDate.ctime()) + " was started " + str((startDate - expectedStartDate).seconds / 60) + " minutes late")
                            if ((expectedEndDate > endDate) and (expectedEndDate - endDate).seconds / 60) > 5: # if left 5 minutes or more early
                                reports.append(name + ": This shift on " + str(expectedStartDate.ctime()) + " was left " + str((expectedEndDate - endDate).seconds / 60) + " minutes early")
                            break
                            

                if i == len(responseData) -1:
                    reports.append(name + ": This shift on " + str(expectedStartDate.ctime()) + " was not made.") 
                
    return reports

def sameDates(start, expectedStart):
    return start.date() == expectedStart.date()
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