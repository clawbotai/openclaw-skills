import { LightningElement, wire, api } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import getPendingReviews from '@salesforce/apex/AzothDoctorController.getPendingReviews';
import getRecentOrders from '@salesforce/apex/AzothDoctorController.getRecentOrders';
import getRelatedTasks from '@salesforce/apex/AzothDoctorController.getRelatedTasks';
import getUpcomingAppointments from '@salesforce/apex/AzothDoctorController.getUpcomingAppointments';
import getDoctorProfile from '@salesforce/apex/AzothDoctorController.getDoctorProfile';

const REVIEW_COLUMNS = [
    { label: 'Review ID', fieldName: 'Name' },
    { label: 'Status', fieldName: 'Status__c' },
    { label: 'Date Assigned', fieldName: 'CreatedDate', type: 'date' },
    { label: 'Action', type: 'button', typeAttributes: { label: 'VOTE', name: 'vote', variant: 'brand-outline', class: 'sovereign-btn' } }
];

const ORDER_COLUMNS = [
    { label: 'Order Number', fieldName: 'OrderNumber' },
    { label: 'Patient', fieldName: 'AccountName' }, // Flattened in wire
    { label: 'Status', fieldName: 'Status' },
    { label: 'Amount', fieldName: 'TotalAmount', type: 'currency' },
    { label: 'Action', type: 'button', typeAttributes: { label: 'Activate', name: 'activate', variant: 'brand', class: 'slds-m-left_x-small' } }
];

const APPT_COLUMNS = [
    { label: 'Subject', fieldName: 'Subject' },
    { label: 'Related To', fieldName: 'WhatName' },
    {
        label: 'Time', fieldName: 'StartDateTime', type: 'date', typeAttributes: {
            year: "numeric", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit"
        }
    }
];

const TASK_COLUMNS = [
    { label: 'Subject', fieldName: 'Subject' },
    { label: 'Related To', fieldName: 'WhatName' },
    { label: 'Priority', fieldName: 'Priority' },
    { label: 'Due Date', fieldName: 'ActivityDate', type: 'date' },
    { label: 'Action', type: 'button', typeAttributes: { label: 'Complete', name: 'complete_task', variant: 'brand', class: 'slds-m-left_x-small' } }
];

export default class DoctorDashboardClean extends NavigationMixin(LightningElement) {
    @api recordId; // Injected by Record Page

    reviewColumns = REVIEW_COLUMNS;
    orderColumns = ORDER_COLUMNS;
    apptColumns = APPT_COLUMNS;
    taskColumns = TASK_COLUMNS;

    rawOrders = [];
    rawAppointments = [];
    rawTasks = [];

    // --- Reviews ---
    @wire(getPendingReviews)
    wiredReviews({ error, data }) {
        if (data) {
            this.reviews = data;
            this.reviewError = undefined;
        } else if (error) {
            this.reviews = undefined;
            this.reviewError = JSON.stringify(error);
            console.error('Error loading reviews', JSON.stringify(error));
        }
    }
    reviewError = null;

    // --- Tasks ---
    @wire(getRelatedTasks)
    wiredTasks({ error, data }) {
        if (data) {
            this.rawTasks = data.map(row => ({
                ...row,
                WhatName: row.What ? row.What.Name : (row.Who ? row.Who.Name : '')
            }));
            this.taskError = undefined;
        } else if (error) {
            console.error('Error loading tasks', error);
            this.taskError = JSON.stringify(error);
        }
    }
    taskError;

    // --- Appointments ---
    @wire(getUpcomingAppointments, { doctorId: '$recordId' })
    wiredAppointments({ error, data }) {
        if (data) {
            this.rawAppointments = data.map(row => ({
                ...row,
                WhatName: row.What ? row.What.Name : (row.Who ? row.Who.Name : '')
            }));
        } else if (error) {
            console.error('Error fetching appointments', error);
        }
    }

    // --- Orders ---
    @wire(getRecentOrders)
    wiredOrders({ error, data }) {
        if (data) {
            // Flatten Account.Name for Datatable
            this.rawOrders = data.map(row => ({
                ...row,
                AccountName: row.Account ? row.Account.Name : ''
            }));
        } else if (error) {
            console.error(error);
        }
    }

    // --- Getters ---
    get pendingCount() {
        return this.reviews ? this.reviews.length : 0;
    }

    get taskCount() {
        return this.rawTasks ? this.rawTasks.length : 0;
    }

    // --- Actions ---
    handleRowAction(event) {
        const actionName = event.detail.action.name;
        const row = event.detail.row;

        if (actionName === 'complete_task') {
            this.navigateToTaskValidation(row.Id);
        } else if (actionName === 'activate') {
            // Existing order activation logic (placeholder if needed)
            console.log('Activate Order', row.Id);
        } else if (actionName === 'vote') {
            // Vote logic
        }
    }

    navigateToTaskValidation(taskId) {
        // Navigate to the Flow, passing the Task ID
        // Note: For Experience Cloud, direct URL navigation is often most reliable for Flows
        this[NavigationMixin.Navigate]({
            type: 'standard__webPage',
            attributes: {
                url: '/flow/Patient_Validation?recordId=' + taskId
            }
        });
    }

    // --- Profile ---
    @wire(getDoctorProfile)
    wiredDoctorProfile({ error, data }) {
        if (data) {
            this.doctorProfile = data;
            this.profileError = undefined;
        } else if (error) {
            this.doctorProfile = undefined;
            this.profileError = JSON.stringify(error);
            console.error('Error loading doctor profile', JSON.stringify(error));
        }
    }
    doctorProfile;
    profileError;
}