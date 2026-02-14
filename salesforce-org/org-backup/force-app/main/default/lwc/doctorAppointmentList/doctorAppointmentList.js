import { LightningElement, wire } from 'lwc';
import getUpcomingAppointments from '@salesforce/apex/AzothDoctorController.getUpcomingAppointments';

const COLUMNS = [
    { label: 'Subject', fieldName: 'Subject', type: 'text' },
    { label: 'Related To', fieldName: 'WhatIdx', type: 'text' },
    {
        label: 'Time', fieldName: 'StartDateTime', type: 'date',
        typeAttributes: {
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit"
        }
    }
];

export default class DoctorAppointmentList extends LightningElement {
    columns = COLUMNS;
    appointments = [];

    @wire(getUpcomingAppointments)
    wiredAppointments({ error, data }) {
        if (data) {
            this.appointments = data.map(row => ({
                ...row,
                WhatIdx: row.What ? row.What.Name : ''
            }));
        } else if (error) {
            console.error(error);
        }
    }
}