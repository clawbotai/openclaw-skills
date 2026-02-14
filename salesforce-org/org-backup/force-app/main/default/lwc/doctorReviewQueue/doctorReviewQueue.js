import { LightningElement, wire, track } from 'lwc';
import getPendingReviews from '@salesforce/apex/AzothDoctorController.getPendingReviews';
import submitVote from '@salesforce/apex/DoctorPortalController.submitVote';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { refreshApex } from '@salesforce/apex';

const COLUMNS = [
    { label: 'Review ID', fieldName: 'Name', type: 'text' },
    { label: 'Order', fieldName: 'OrderNumber', type: 'text' },
    { label: 'Status', fieldName: 'Status__c', type: 'text' },
    { label: 'Date Assigned', fieldName: 'CreatedDate', type: 'date' },
    {
        type: 'button',
        typeAttributes: { label: 'Review', name: 'review', variant: 'brand' }
    }
];

export default class DoctorReviewQueue extends LightningElement {
    columns = COLUMNS;
    @track reviews = [];
    wiredReviewsResult;

    @track showModal = false;
    @track selectedReview = {};

    @wire(getPendingReviews)
    wiredReviews(result) {
        this.wiredReviewsResult = result;
        const { error, data } = result;
        if (data) {
            this.reviews = data.map(row => ({
                ...row,
                OrderNumber: row.Order__r ? row.Order__r.OrderNumber : ''
            }));
        } else if (error) {
            this.showToast('Error', 'Error loading reviews', 'error');
            console.error(error);
        }
    }

    handleRowAction(event) {
        const row = event.detail.row;
        this.selectedReview = {
            Id: row.Id,
            Name: row.Name,
            OrderName: row.OrderNumber
        };
        this.showModal = true;
    }

    closeModal() {
        this.showModal = false;
    }

    handleApprove() {
        this.submitDecision('1');
    }

    handleReject() {
        this.submitDecision('-1');
    }

    submitDecision(vote) {
        submitVote({ recordId: this.selectedReview.Id, vote: vote })
            .then(() => {
                this.showToast('Success', 'Vote submitted successfully', 'success');
                this.showModal = false;
                return refreshApex(this.wiredReviewsResult);
            })
            .catch(error => {
                this.showToast('Error', error.body.message, 'error');
            });
    }

    showToast(title, message, variant) {
        this.dispatchEvent(new ShowToastEvent({ title, message, variant }));
    }
}