#include <bits/stdc++.h>
using namespace std;
#define ll long long

const int N = 2e5+1;
vector<ll> seg(4*N);
vector<int> v(N+1);

ll build(int node, int l, int r){
    if(l == r) return seg[node] = v[l];
    ll mid = (l+r)/2;
    return  seg[node] = build(node*2, l, mid) + build(node*2+1, mid+1, r);    
}

ll update(int node, int l, int r, int i){
    if(i < l || i > r) return seg[node];
    if(l == r && l == i) return seg[node] = v[i];
    ll mid = (r+l)/2;
    return seg[node] = (update(node*2, l, mid, i) + update(node*2+1, mid+1, r, i));
}

ll check(int node, int l, int r, int lb, int rb){
    if(r < lb || l > rb) return 0;
    if(l >= lb && r <= rb) return seg[node];
    ll mid = (l+r)/2;
    return check(node*2, l, mid, lb, rb) + check(node*2+1, mid+1, r, lb, rb);
}

int main(){
    ios::sync_with_stdio(false);
    cin.tie(NULL);
    int n, q;
    cin >> n >> q;
    for(int i = 1; i <= n; i++){
        cin >> v[i];
    }
    build(1, 1, n);
    for(int i = 0; i < q; i++){
        int query;
        cin >> query;
        if(query == 1){
            int a, b;
            cin >> a >> b;
            v[a] = b;
            update(1, 1, n, a);
        } else{
            int a, b;
            cin >> a >> b;
            cout << (check(1, 1, n, a, b)) << "\n";
        }
    }
}
