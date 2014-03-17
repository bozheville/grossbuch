
var controller = function($scope, $http, $cookieStore){
    $scope.showPopup = {TRFilters: false, TRUsers: false};
    $scope.base_url = 'http://tuugobank.grybov.com/';

    $scope.transactionfilters = {
        filters:{
            debit:true,
            payout:true,
            credit:true,
            repayment:true
        },
        users:{}
    };

    var initNew = function(e){
        $scope.pageinfo = e;
        $scope.saveduser = $cookieStore.get('user');
        for(user in $scope.pageinfo.users){
            var uid = $scope.pageinfo.users[user]._id;
            $scope.transactionfilters.users[uid] = true;
        }
        $scope.newTransaction = {
            type : 'debit',
            name : $scope.saveduser,
            amount: 20
        };
        $scope.newTransaction.date = $scope.newTransaction.date.replace(/(^|[.])([1-9])(?=\.)/g, '$10$2');
    };

    var initPage = function(){
        $http.get($scope.base_url + 'api/getinfo').success(function(e){
            initNew(e);
        });
    };

    $scope.processTransaction = function(){
        var errors = [];
        if(['debit', 'credit','repayment', 'payout'].indexOf($scope.newTransaction.type) == -1){errors.push('type');}
        if(!$scope.newTransaction.name){errors.push('name');}
        if(!String($scope.newTransaction.amount).match(/^\d+$/)){errors.push('amount');}
        if(errors.length == 0){
            $http.get($scope.base_url + 'api/newTransaction/'+$scope.newTransaction.name+'/'+$scope.newTransaction.type+'/'+$scope.newTransaction.amount).success(function(e){
                $cookieStore.put('user', $scope.newTransaction.name);
                initNew(e);
            });
        } else {
            alert('Error in keys: ' + errors.join(', '));
        }
    };

    $scope.setAmount = function(sum){
        $scope.newTransaction.amount=sum;
    };

    $scope.togglePopup = function(type){
        $scope.showPopup[type] = !$scope.showPopup[type];
    };

    $scope.toggleUser = function(_id, value){
        value = value ? 1:0;
        $http.get($scope.base_url + 'api/toggleUser/'+_id+'/'+value);
    };

    initPage();

};

angular.module('tuugobank', ['ngCookies']);