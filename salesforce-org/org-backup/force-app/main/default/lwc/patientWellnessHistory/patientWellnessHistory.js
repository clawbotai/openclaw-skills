import { LightningElement, wire } from 'lwc';
import getMyIntakes from '@salesforce/apex/AzothPatientController.getMyIntakes';

const COLUMNS = [
    { label: 'Report Name', fieldName: 'Name', type: 'text' },
    { label: 'Type', fieldName: 'Type__c', type: 'text' },
    { label: 'Date', fieldName: 'CreatedDate', type: 'date' }
];

export default class PatientWellnessHistory extends LightningElement {
    columns = COLUMNS;
    intakes = [];

    @wire(getMyIntakes)
    wiredIntakes({ error, data }) {
        if (data) {
            this.intakes = data;
        } else if (error) {
            console.error(error);
        }
    }
}