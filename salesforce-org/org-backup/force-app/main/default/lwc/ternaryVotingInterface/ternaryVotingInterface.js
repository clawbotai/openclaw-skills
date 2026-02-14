import { LightningElement, api, wire } from 'lwc';
import { getRecord, getFieldValue } from 'lightning/uiRecordApi';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import submitVote from '@salesforce/apex/DoctorPortalController.submitVote';
import STATUS_FIELD from '@salesforce/schema/Peer_Review__c.Status__c';

export default class TernaryVotingInterface extends LightningElement {
    @api recordId;
    verdict = 0;
    isLoading = false;
    isLocked = false;

    @wire(getRecord, { recordId: '$recordId', fields: [STATUS_FIELD] })
    wiredRecord({ error, data }) {
        if (data) {
            const status = getFieldValue(data, STATUS_FIELD);
            this.isLocked = (status === 'Completed');
        } else if (error) {
            console.error('Error fetching record status:', error);
        }
    }

    handleVeto() { if (!this.isLocked) this.updateVerdict(-1); }
    handleNeutral() { if (!this.isLocked) this.updateVerdict(0); }
    handleApprove() { if (!this.isLocked) this.updateVerdict(1); }

    updateVerdict(val) {
        this.verdict = val;
    }

    get buttonClassVeto() { return `vote-btn veto ${this.verdict === -1 ? 'active' : ''}`; }
    get buttonClassNeutral() { return `vote-btn neutral ${this.verdict === 0 ? 'active' : ''}`; }
    get buttonClassApprove() { return `vote-btn approve ${this.verdict === 1 ? 'active' : ''}`; }

    async handleSubmit() {
        if (this.isLocked) return;
        this.isLoading = true;

        let voteValue = '0';
        if (this.verdict === 1) voteValue = '+1';
        if (this.verdict === -1) voteValue = '-1';

        try {
            await submitVote({ recordId: this.recordId, vote: voteValue });

            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Success',
                    message: 'Verdict sealed successfully',
                    variant: 'success'
                })
            );
            this.isLocked = true;

            // Optional: Refresh view to update standard components
            // notifyRecordUpdateAvailable([{recordId: this.recordId}]); 

        } catch (error) {
            console.error('Voting Error:', error);
            this.dispatchEvent(
                new ShowToastEvent({
                    title: 'Error',
                    message: error.body ? error.body.message : error.message,
                    variant: 'error'
                })
            );
        } finally {
            this.isLoading = false;
        }
    }
}