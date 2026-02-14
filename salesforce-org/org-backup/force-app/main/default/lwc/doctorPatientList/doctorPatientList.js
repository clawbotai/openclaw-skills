import { LightningElement, wire } from 'lwc';
import getMyPatients from '@salesforce/apex/AzothDoctorController.getMyPatients';

const COLUMNS = [
    { label: 'Patient Name', fieldName: 'Name', type: 'text' },
    { label: 'Phone', fieldName: 'Phone', type: 'phone' },
    { label: 'City', fieldName: 'BillingCity', type: 'text' },
    { label: 'Created', fieldName: 'CreatedDate', type: 'date' }
];

export default class DoctorPatientList extends LightningElement {
    columns = COLUMNS;
    patients = [];

    @wire(getMyPatients)
    wiredPatients({ error, data }) {
        if (data) {
            this.patients = data;
        } else if (error) {
            console.error(error);
        }
    }
}