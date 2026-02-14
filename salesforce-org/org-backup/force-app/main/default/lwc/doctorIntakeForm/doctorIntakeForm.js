import { LightningElement, track } from 'lwc';
import submitApplication from '@salesforce/apex/AzothDoctorIntakeController.submitDoctorApplication';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';

export default class DoctorIntakeForm extends LightningElement {
    @track firstName = '';
    @track lastName = '';
    @track email = '';
    @track phone = '';
    @track medicalLicense = '';
    @track agreedToTerms = false;

    @track isLoading = false;
    @track isSuccess = false;
    @track errorMessage;

    handleInputChange(event) {
        const field = event.target.dataset.field;
        const value = event.target.type === 'checkbox' ? event.target.checked : event.target.value;
        this[field] = value;
    }

    validate() {
        if (!this.firstName || !this.lastName || !this.email || !this.medicalLicense || !this.agreedToTerms) {
            this.errorMessage = 'Please fill in all required fields and agree to terms.';
            return false;
        }
        this.errorMessage = null;
        return true;
    }

    handleSubmit() {
        if (!this.validate()) return;

        this.isLoading = true;
        const data = {
            firstName: this.firstName,
            lastName: this.lastName,
            email: this.email,
            phone: this.phone,
            medicalLicense: this.medicalLicense
        };

        submitApplication({ doctorData: data })
            .then(result => {
                this.isSuccess = true;
                this.showToast('Success', 'Registration submitted successfully', 'success');
            })
            .catch(error => {
                console.error('Error', error);
                this.errorMessage = error.body ? error.body.message : 'Unknown Error';
                this.showToast('Error', this.errorMessage, 'error');
            })
            .finally(() => {
                this.isLoading = false;
            });
    }

    showToast(title, message, variant) {
        this.dispatchEvent(new ShowToastEvent({ title, message, variant }));
    }
}