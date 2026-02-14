import { LightningElement, wire } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import getWellnessAssessments from '@salesforce/apex/AzothDoctorController.getWellnessAssessments';

const COLUMNS = [
    { label: 'Assessment', fieldName: 'Name', type: 'text' },
    { label: 'Patient', fieldName: 'PatientIdx', type: 'text' }, // Flattened
    { label: 'Type', fieldName: 'Type__c', type: 'text' },
    { label: 'Date', fieldName: 'CreatedDate', type: 'date' },
    {
        label: 'Action',
        type: 'button',
        typeAttributes: {
            label: 'View',
            name: 'view_assessment',
            variant: 'base'
        }
    }
];

export default class DoctorWellnessList extends NavigationMixin(LightningElement) {
    columns = COLUMNS;
    assessments = [];

    @wire(getWellnessAssessments)
    wiredAssessments({ error, data }) {
        if (data) {
            this.assessments = data.map(row => ({
                ...row,
                PatientIdx: row.Patient__r ? row.Patient__r.Name : ''
            }));
        } else if (error) {
            console.error(error);
        }
    }

    handleRowAction(event) {
        const actionName = event.detail.action.name;
        const row = event.detail.row;

        if (actionName === 'view_assessment') {
            this.navigateToRecord(row.Id);
        }
    }

    navigateToRecord(recordId) {
        this[NavigationMixin.GenerateUrl]({
            type: 'standard__recordPage',
            attributes: {
                recordId: recordId,
                actionName: 'view'
            }
        }).then(url => {
            window.open(url, '_blank');
        });
    }
}