import { LightningElement, wire } from 'lwc';
import getMyAppointments from '@salesforce/apex/AzothPatientController.getMyAppointments';

const COLUMNS = [
    { label: 'Subject', fieldName: 'Subject', type: 'text' },
    { label: 'Doctor', fieldName: 'OwnerName', type: 'text' },
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

export default class PatientAppointmentList extends LightningElement {
    columns = COLUMNS;
    appointments = [];

    @wire(getMyAppointments)
    wiredAppointments({ error, data }) {
        if (data) {
            this.appointments = data.map(row => ({
                ...row,
                OwnerName: row.Owner ? row.Owner.Name : ''
            }));
        } else if (error) {
            console.error(error);
        }
    }
}