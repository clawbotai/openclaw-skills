import { LightningElement, wire } from 'lwc';
import getRecentOrders from '@salesforce/apex/AzothDoctorController.getRecentOrders';
import activateOrder from '@salesforce/apex/AzothDoctorController.activateOrder';
import { ShowToastEvent } from 'lightning/platformShowToastEvent';
import { refreshApex } from '@salesforce/apex';

const COLUMNS = [
    { label: 'Order Number', fieldName: 'OrderNumber', type: 'text' },
    { label: 'Patient', fieldName: 'AccountName', type: 'text' },
    { label: 'Status', fieldName: 'Status', type: 'text' },
    { label: 'Amount', fieldName: 'TotalAmount', type: 'currency' },
    {
        type: 'button',
        typeAttributes: {
            label: 'Activate',
            name: 'activate',
            title: 'Activate Order',
            disabled: { fieldName: 'isNotDraft' },
            variant: 'brand'
        }
    }
];

export default class DoctorOrderList extends LightningElement {
    columns = COLUMNS;
    orders = [];
    wiredOrdersResult;

    @wire(getRecentOrders)
    wiredOrders(result) {
        this.wiredOrdersResult = result;
        const { error, data } = result;
        if (data) {
            this.orders = data.map(order => ({
                ...order,
                AccountName: order.Account ? order.Account.Name : '',
                isNotDraft: order.Status !== 'Draft'
            }));
        } else if (error) {
            console.error(error);
        }
    }

    handleRowAction(event) {
        const actionName = event.detail.action.name;
        const row = event.detail.row;
        switch (actionName) {
            case 'activate':
                this.activateOrder(row.Id);
                break;
            default:
        }
    }

    activateOrder(orderId) {
        activateOrder({ orderId: orderId })
            .then(() => {
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Success',
                        message: 'Order activated successfully',
                        variant: 'success'
                    })
                );
                return refreshApex(this.wiredOrdersResult);
            })
            .catch(error => {
                this.dispatchEvent(
                    new ShowToastEvent({
                        title: 'Error activating order',
                        message: error.body ? error.body.message : error.message,
                        variant: 'error'
                    })
                );
            });
    }
}