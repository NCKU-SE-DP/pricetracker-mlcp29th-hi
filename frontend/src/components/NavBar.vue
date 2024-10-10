<template>
    <nav class="navbar">
        <div class="title"> <RouterLink to="/overview">價格追蹤小幫手</RouterLink></div>
        <transition :css="animated">
            <ul class="options" v-show="!isSmallScreen || isMenuExpanded" @click="isSmallScreen ? toggleDropdownMenu() : null">
                <li><RouterLink to="/overview"><i class="bi bi-speedometer2"></i>物價概覽</RouterLink></li>
                <li><RouterLink to="/trending"><i class="bi bi-graph-up"></i>物價趨勢</RouterLink></li>
                <li><RouterLink to="/news"><i class="bi bi-megaphone"></i>相關新聞</RouterLink></li>
                <li v-if="!isLoggedIn"><RouterLink to="/login"><i class="bi bi-person"></i>登入</RouterLink></li>
                <li v-else @click="logout"><span>Hi, {{getUserName}}! 登出</span></li>
            </ul>
        </transition>
        <button class="hamburger" v-show="isSmallScreen" @click="toggleDropdownMenu">
            <i v-if="isMenuExpanded" class="bi bi-chevron-up"></i>
            <i v-else class="bi bi-list"></i>
        </button>
    </nav>
</template>

<script>
import { useAuthStore } from '@/stores/auth';

export default {
    name: 'NavBar',
    data() {
        return {
            isSmallScreen: false,
            isMenuExpanded: false,
            animated: true
        }
    },
    computed: {
        isLoggedIn(){
            const userStore = useAuthStore();
            return userStore.isLoggedIn;
        },
        getUserName(){
            const userStore = useAuthStore();
            return userStore.getUserName;
        }
    },
    watch: {
        isSmallScreen(isSmall) {
            this.animated = false;
            if (!isSmall) {
                this.isMenuExpanded = false;
            }
            setTimeout(() => {
                this.animated = true
            }, 100);
        }
    },
    methods: {
        logout(){
            const userStore = useAuthStore();
            userStore.logout();
        },
        toggleDropdownMenu() {
            this.isMenuExpanded = !this.isMenuExpanded;
        },
        checkScreenSize(e) {
            this.isSmallScreen = window.innerWidth <= 768;
        }
    },
    mounted() {
        this.checkScreenSize();
        window.addEventListener("resize", this.checkScreenSize);
    },
    unmounted() {
        window.removeEventListener("resize", this.checkScreenSize);
    }
};
</script>

<style scoped>
.navbar {
    display: flex;
    justify-content: space-between;
    background-color: #f3f3f3;
    padding: 1.5em;
    height: 4.5em;
    width: 100%;
    align-items: center;
    box-shadow: 0 0 5px #000000;
}

.navbar ul {
    list-style: none;
    display: flex;
    justify-content: space-around;
}

.title {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.title > a{
    font-size: 1.4em;
    font-weight: bold;
    color: #2c3e50 !important;
}

.navbar li {
    display: flex;
    color: #575B5D;
    margin: 0 .5em;
    font-size: 1.2em;
}

.navbar li:hover {
    cursor: pointer;
    font-weight: bold;
}

.navbar li i {
    margin-right: 0.25em;
}

.navbar li:hover i {
    -webkit-text-stroke: 0.75px;
}

.navbar a {
    text-decoration: none;
    color: #575B5D;
}

.navbar .hamburger {
    font-size: 24px;
}

.v-enter-active, .v-leave-active {
    transition: opacity 0.5s;
}

.v-enter-from, .v-leave-to {
    opacity: 0;
}

.v-enter-to, .v-leave-from {
    opacity: 1;
}

@media screen and (max-width: 768px) {
    .navbar ul {
        box-shadow: 0 5px 5px -5px #000000;
    }

    .navbar li {
        margin: 0;
        border-top: 1px solid #e6e6e6;
        background-color: #f3f3f3;
    }

    .navbar li > a,
    .navbar li > span {
        padding: .5em;
        width: 100%;
    }

    .navbar .options {    
        position: absolute;
        top: 4.5em;
        left: 0;
        width: 100%;
        flex-direction: column;
    }
}
</style>