import { LightningElement, wire, track } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import getRelatedTasks from '@salesforce/apex/AzothDoctorController.getRelatedTasks';

const COLUMNS = [
    { label: 'Subject', fieldName: 'Subject' },
    { label: 'Related To', fieldName: 'WhatName' },
    { label: 'Priority', fieldName: 'Priority' },
    { label: 'Due Date', fieldName: 'ActivityDate', type: 'date' },
    {
        label: 'Assessment',
        type: 'button',
        typeAttributes: {
            label: 'View Assessment',
            name: 'view_assessment',
            variant: 'base',
            disabled: { fieldName: 'noAssessment' }
        }
    },
    { label: 'Action', type: 'button', typeAttributes: { label: 'Complete', name: 'complete_task', variant: 'brand', class: 'slds-m-left_x-small' } }
];

export default class DoctorTaskList extends NavigationMixin(LightningElement) {
    @track tasks = [];
    @track error;
    columns = COLUMNS;

    @wire(getRelatedTasks)
    wiredTasks({ error, data }) {
        if (data) {
            this.tasks = data.map(row => ({
                ...row,
                WhatName: row.WhatName, // Already flattened in Apex
                noAssessment: !row.AssessmentId
            }));
            this.error = undefined;
        } else if (error) {
            this.error = JSON.stringify(error);
            this.tasks = [];
        }
    }

    get taskCount() {
        return this.tasks ? this.tasks.length : 0;
    }

    handleRowAction(event) {
        const actionName = event.detail.action.name;
        const row = event.detail.row;

        if (actionName === 'complete_task') {
            this.navigateToTaskValidation(row.Id);
        } else if (actionName === 'view_assessment') {
            this.navigateToRecord(row.AssessmentId);
        }
    }

    navigateToTaskValidation(taskId) {
        this[NavigationMixin.Navigate]({
            type: 'standard__webPage',
            attributes: {
                url: '/flow/Patient_Validation?recordId=' + taskId
            }
        });
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

    handleViewAll() {
        // Placeholder for view all list view navigation
    }
}