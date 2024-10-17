<template>
    <div class="wrapper">
        <h1>物價趨勢</h1>
        <div class="content">
            <div class="selects">

                <select v-model="selectedCategory">
                    <option disabled value="">請選擇商品類別</option>
                    <option v-for="category in categoryKeys" :key="category" :value="category">{{
                        categoryName(category)}}</option>
                </select>
                <select v-model="selectedProduct" :disabled="selectedCategory === ''">
                    <option disabled value="">{{this.selectedCategory === '' ? '再選擇商品' : '請選擇商品'}}</option>
                    <option v-for="product in products" :key="product.產品名稱" :value="product">{{ product.產品名稱 }}</option>
                </select>
            </div>
            <div v-if="selectedProduct" class="visualize">
                <TrendingChart v-if="selectedProduct" :data="selectedProduct"></TrendingChart>
                <TrendingTable v-if="selectedProduct" :data="selectedProduct"></TrendingTable>
            </div>
        </div>
    </div>
</template>

<script>
import { usePricesStore } from '@/stores/prices';
import Categories from '@/constants/categories';
import TrendingTable from '@/components/TrendingTable.vue';
import TrendingChart from '@/components/TrendingChart.vue';

export default {
    components: {
        TrendingTable,
        TrendingChart
    },
    data() {
        return {
            selectedCategory: '',
            selectedProduct: '',
            productList: [],
        };
    },
    computed: {
        store() {
            return usePricesStore();
        },
        categoryKeys() {
            return Object.keys(Categories);
        },
        products() {
            return this.selectedCategory ? this.store.getPricesByCategory(this.selectedCategory) : [];
        },
    },
    methods: {
        categoryName(category) {
            return Categories[category];
        }
    },
    watch: {
        selectedCategory() {
            this.selectedProduct = '';
            const store = usePricesStore();
            this.productList = store.getProductList(this.selectedCategory);
            this.productData = null;
        },
        selectedProduct() {
            console.log(this.selectedProduct);
        }
    },
    created() {
        const store = usePricesStore();
        store.fetchPrices();
    }
};
</script>


<style scoped>
.content {
    margin-top: 2em;
    background-color: #fff;
    border-radius: 1em;
    border: 2em solid #fff;
    width: 100%;
}


.selects {
    display: flex;
    justify-content: flex-start;
    flex-wrap: wrap;
}

.selects>select {
    padding: .5em;
    font-size: 1.1em;
    margin-right: 1em;
    margin: 0.25em 1em 0.25em 0;
    border-radius: .5em;
    border: 1px solid #ccc;
    outline: none;
    cursor: pointer;
    appearance: auto;
    max-width: 100%;
    text-overflow: ellipsis;
}

.visualize > * {
    flex: 1 1 50%;
    box-sizing: border-box;
    border: 1em solid #fff;
}
</style>