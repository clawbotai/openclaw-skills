import { LightningElement, api, wire } from 'lwc';
import { getRelatedListRecords } from 'lightning/uiRelatedListApi';

export default class PatientDashboard extends LightningElement {
    @api recordId; // User or Patient Record Id

    @wire(getRelatedListRecords, {
        parentRecordId: '$recordId',
        relatedListId: 'Orders', // Assuming the relationship name is Orders
        fields: ['Order.OrderNumber', 'Order.Status', 'Order.TotalAmount']
    })
    wiredOrders;

    get orders() {
        return this.wiredOrders.data ? this.wiredOrders.data.records.map(r => ({
            Id: r.id,
            OrderNumber: r.fields.OrderNumber.value,
            Status: r.fields.Status.value,
            TotalAmount: r.fields.TotalAmount.value
        })) : [];
    }
}