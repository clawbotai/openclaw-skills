import { LightningElement } from 'lwc';
import { NavigationMixin } from 'lightning/navigation';
import getHubRecord from '@salesforce/apex/DoctorPortalController.getHubRecord';

export default class DoctorHubRedirect extends NavigationMixin(LightningElement) {
    connectedCallback() {
        this.redirectToHub();
    }

    async redirectToHub() {
        try {
            const hubInfo = await getHubRecord();

            if (hubInfo && hubInfo.recordId) {
                // Determine which object page to navigate to
                const objectApiName = hubInfo.recordType === 'Doctor' ? 'Doctor__c' : 'Account';

                // Redirect to the appropriate hub page
                this[NavigationMixin.Navigate]({
                    type: 'standard__recordPage',
                    attributes: {
                        recordId: hubInfo.recordId,
                        objectApiName: objectApiName,
                        actionName: 'view'
                    }
                });
                // console.log('Hub identified but redirect disabled per config:', hubInfo);
            } else {
                // No hub record found - user might be internal admin
                console.log('No Doctor or Patient record linked to this user');
            }
        } catch (error) {
            console.error('Error redirecting to hub:', error);
        }
    }
}