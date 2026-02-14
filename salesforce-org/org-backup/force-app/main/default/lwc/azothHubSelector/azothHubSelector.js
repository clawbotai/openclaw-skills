import { LightningElement, wire, api } from 'lwc';
import getHubRecord from '@salesforce/apex/DoctorPortalController.getHubRecord';
import { NavigationMixin } from 'lightning/navigation';

export default class AzothHubSelector extends NavigationMixin(LightningElement) {
    @api viewMode = 'Auto';
    @api patientFlowApiName = 'Request_Doctor_Appointment';

    showDoctor = false;
    showPatient = false;
    isLoading = true;
    message = 'Resolving Access...';

    @wire(getHubRecord)
    wiredHub({ error, data }) {
        if (this.viewMode !== 'Auto') {
            this.handleManualOverride();
            return;
        }

        if (data) {
            this.handleRouting(data);
        } else if (error) {
            this.isLoading = false;
            // Display raw error for debugging
            this.message = 'Trace: ' + (error.body ? error.body.message : error.message);
            console.error('Hub Selection Error:', error);
        } else if (!data && !error) {
            // Null data means neither Doctor nor Patient found
            this.isLoading = false;
            this.message = 'No access found. You are not registered as a Doctor or Patient.';
        }
    }

    handleRouting(hubInfo) {
        if (hubInfo.recordType === 'Doctor') {
            this.showDoctor = true;
            this.message = '';
            this.isLoading = false;
        } else if (hubInfo.recordType === 'Patient') {
            this.showPatient = true;
            this.message = '';
            this.isLoading = false;
        } else {
            this.message = 'Unknown Profile Type: ' + hubInfo.recordType;
            this.isLoading = false;
        }
    }

    handleManualOverride() {
        this.isLoading = false;
        this.message = '';
        if (this.viewMode === 'Doctor') {
            this.showDoctor = true;
            this.showPatient = false;
        } else if (this.viewMode === 'Patient') {
            this.showPatient = true;
            this.showDoctor = false;
        }
    }
}