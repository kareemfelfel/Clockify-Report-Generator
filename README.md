## Purpose:
- This report generator connects to the Clockify reports API endpoint using the ID of the workspace
> 'https://reports.api.clockify.me/v1/workspaces/{id}/reports/detailed'
- The data is received and stored in a dictionary.
- data is read from the file ``` schedule.json ``` and a dictionary is made for each user in the schedule
where: for every user, their schedule corresponds with a date and a start/end time in ISO 8601 format.
- For example, for a user that works every Monday from x -> z:
	- A report is generated for every monday in the calendar from the entered start date in ``` data.json ``` to the entered end date in ``` data.json ```
	- Holidays from ``` holidays.json ``` are ignored in the scheduled (not added)
- Finally the generator makes a report on each user stating the day and shift where the employee was late, did not report to work, or left early.

## Useage:
- Clone repository.
- cd to cloned directory.
- use command ``` python ReportGenerator.py ``` to run the file.

## data.json:
- contains the workspaceID, key to API, start date, and end date.
- NOTE:
	- Dates must be in this format: YYYY-MM-DD

## schedule.json:
- contains all students and their schedules.
- NOTE:
	- All days must be typed as week days: Monday, Tuesday, etc.
	- start and end must be in this format: 11:00 AM
	- email must correspond to the same email that the user uses on Clockify
- ```timeMarginOfError``` is the free time measured in minutes that you give to the employees so they have time to log in to clockify or if they are late for any possible reason.
This time can account for errors, technology lags, etc.

## holidays.json:
- contains all holidays as objects in holidays array.
- NOTE:
	- Dates must be in this format: YYYY-MM-DD