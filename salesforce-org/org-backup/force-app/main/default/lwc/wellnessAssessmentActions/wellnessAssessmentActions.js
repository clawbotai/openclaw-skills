import { LightningElement, api, wire, track } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import { NavigationMixin } from 'lightning/navigation';
import PATIENT_STATUS_FIELD from '@salesforce/schema/Wellness_Assessment__c.Patient__r.Validation_Status__c';

const FIELDS = [PATIENT_STATUS_FIELD];

export default class WellnessAssessmentActions extends NavigationMixin(LightningElement) {
    @api recordId;
    @track showButton = false;

    @wire(getRecord, { recordId: '$recordId', fields: FIELDS })
    wiredRecord({ error, data }) {
        if (data) {
            const status = getFieldValue(data, PATIENT_STATUS_FIELD);
            this.showButton = status !== 'Validated';
        } else if (error) {
            console.error('Error loading assessment', error);
        }
    }

    handleValidate() {
        // Launch the Flow directly
        this[NavigationMixin.Navigate]({
            type: 'standard__webPage',
            attributes: {
                url: '/flow/Wellness_Assessment_Validation?recordId=' + this.recordId + '&retURL=' + encodeURIComponent(window.location.href)
            }
        });
    }
}