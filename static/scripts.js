// 初期化
document.addEventListener('DOMContentLoaded', () => {
    displayCards([]); // 初期状態で「検索してください」を表示
    updatePaginationButtons(); // 初期化時にボタンを更新
    initTabSwitching(); // タブ切り替え処理の初期化
    setupSearchHandler(); // 検索の初期設定
    populateChannelSelect(); // チャネル選択肢を設定
    populateLevelSelect();
    populateSelect("type-input", "category_title");  // カテゴリの選択肢を設定
    populateSelect("players-input", "players");  // プレイヤー数の選択肢を設定
});

// ユニークな選択肢を取得・設定する関数
function populateSelect(selectId, columnName) {
    fetch(`/get_unique_values/${columnName}`)
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById(selectId);
            select.innerHTML = `<option value="">${selectId === "type-input" ? "カテゴリ" : "プレイヤー数"}を選択</option>`; // 初期値をセット

            const n_vs_n = [];
            const n_people = [];
            const others = [];

            data.forEach(value => {
                let match;
                if ((match = value.match(/^(\d+)対(\d+)$/))) {
                    // "n対n" の形式を解析
                    const num1 = parseInt(match[1], 10);
                    const num2 = parseInt(match[2], 10);
                    n_vs_n.push({ value, num1, num2 });
                } else if ((match = value.match(/^(\d+)人$/))) {
                    // "n人" の形式を解析
                    const num = parseInt(match[1], 10);
                    n_people.push({ value, num });
                } else {
                    // その他の値（例: "人数指定なし" など）
                    others.push(value);
                }
            });

            // 数値順にソート
            n_vs_n.sort((a, b) => a.num1 - b.num1 || a.num2 - b.num2);
            n_people.sort((a, b) => a.num - b.num);
            others.sort(); // それ以外は通常の文字列ソート

            // 並び替えたリストを `<select>` に追加
            [...n_vs_n.map(obj => obj.value), ...n_people.map(obj => obj.value), ...others].forEach(value => {
                const option = document.createElement("option");
                option.value = value;
                option.textContent = value;
                select.appendChild(option);
            });
        })
        .catch(error => console.error(`${columnName} データ取得エラー:`, error));
}




function populateLevelSelect() {
    fetch("/get_levels")
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById("level-input");
            data.forEach(level => {
                const option = document.createElement("option");
                option.value = level.level;
                option.textContent = level.level;
                select.appendChild(option);
            });
        })
        .catch(error => console.error("データ取得エラー:", error));

}

function populateChannelSelect() {
    fetch("/get_channels")
        .then(response => response.json())
        .then(data => {
            const select = document.getElementById("channel-input");
            data.forEach(channel => {
                const option = document.createElement("option");
                option.value = channel.id;
                option.textContent = channel.channel_name;
                select.appendChild(option);
            });
            const ul = document.querySelector(".right-half ul");
            ul.innerHTML = ""; // リストをクリア
            data.forEach(channel => {
                const li = document.createElement("li");
                const a = document.createElement("a");
                a.textContent = channel.channel_name;
                a.href = channel.channel_link; // URLをセット（DBから取得）
                a.target = "_blank"; // 新しいタブで開く
                a.rel = "noopener noreferrer"; // セキュリティ対策
                li.appendChild(a);
                ul.appendChild(li);
            });
        })
        .catch(error => console.error("データ取得エラー:", error));
}

// カード表示用関数
function displayCards(data, limit = 10) {
    const cardContainer = document.querySelector('.card-container');
    const searchPrompt = document.getElementById('search-prompt');

    cardContainer.innerHTML = ''; // 既存のカードをクリア

    if (!data || data.length === 0) {
        searchPrompt.style.display = 'block';
        return;
    }

    searchPrompt.style.display = 'none';
    data.slice(0, limit).forEach(createCard);
}

// カード作成
function createCard(activity) {
    const card = document.createElement('div');
    card.className = 'card';
    card.innerHTML = `
        <div><strong>${activity.title}</strong></div>
        <div class="video-container">
            <iframe src="${activity.video_url}" frameborder="0" allowfullscreen></iframe>
        </div>
        <div class="info">
            <div>アップロード日: ${activity.upload_date}</div>
            <div>再生回数: ${activity.view_count}</div>
            <div>いいね: ${activity.like_count}</div>
            <div>動画時間: ${activity.duration}</div>
            <div>チャネル名: ${activity.channel_category}</div>
        </div>
    `;
    document.querySelector('.card-container').appendChild(card);
}

// 表示中の動画数 / 総動画数を更新
function updateVideoCount(currentCount, totalCount) {
    const videoCountElement = document.getElementById('video-count');
    if (videoCountElement) {
        videoCountElement.innerText = `表示中: ${currentCount} / ${totalCount} 件`;
    }
}

// データ取得処理
function fetchData(endpoint, queryParams, limit) {
    fetch(`${endpoint}?${queryParams}`)
        .then(response => response.json())
        .then(data => {
            displayCards(data.activities, limit);
            totalPages = Math.ceil(data.total / limit); // 総ページ数を計算
            updatePaginationButtons(); // ボタンの状態を更新
            togglePaginationVisibility(data.total);

            updateVideoCount(data.current_display_count, data.total);
        })
        .catch(error => console.error('エラー:', error));
}

// ページング表示制御
function togglePaginationVisibility(totalResults) {
    const pagination = document.querySelector('.pagination');
    //pagination.style.display = totalResults < 11 ? 'none' : 'block';
    pagination.style.display = 'block';
}

// 検索処理
function search(resetPage = true) {
    if (resetPage) currentPage = 1;

    const queryParams = new URLSearchParams({
        q: document.getElementById('search-input').value,
        type: document.getElementById('type-input').value,
        players: document.getElementById('players-input').value,
        level: document.getElementById('level-input').value,
        channel: document.getElementById('channel-input').value,
        sort: document.getElementById('sort-input').value,
        limit: getLimit(),
        offset: (currentPage - 1) * getLimit(),
    }).toString();

    fetchData('/search', queryParams, getLimit());
}

// 入力されたリミットを取得
function getLimit() {
    const limitInput = parseInt(document.getElementById('limit-input').value, 10);
    return isNaN(limitInput) || limitInput <= 0 ? 10 : Math.min(limitInput, 10);
}

let currentPage = 1;
let totalPages = 1;

// ページ変更処理
function goToPage(page) {
    if (page < 1 || page > totalPages) return;
    currentPage = page;
    updatePaginationButtons();
    search(false);
}

// ボタンの有効/無効を更新
function updatePaginationButtons() {
    const prevButton = document.getElementById("prev-page");
    const nextButton = document.getElementById("next-page");
    const currentPageLabel = document.getElementById("current-page");

    prevButton.disabled = currentPage === 1;
    nextButton.disabled = currentPage >= totalPages;
    currentPageLabel.innerText = currentPage;

    if (totalPages === 1) {
        prevButton.disabled = true;
        nextButton.disabled = true;
    }
}

// タブ切り替え処理
function initTabSwitching() {
    const tabButtons = document.querySelectorAll(".tab-button");
    const tabPanels = document.querySelectorAll(".tab-panel");
    const searchContainer = document.querySelector(".search-container");
    const mainContent = document.querySelector(".main-content");
    const paragraphContainer = document.querySelector(".paragraph-container");
    const pagination = document.querySelector(".pagination");

    const typeInput = document.getElementById("type-input");
    const playersInput = document.getElementById("players-input");

    typeInput.addEventListener("change", () => {
        playersInput.disabled = typeInput.value !== "対人";
    });

    tabButtons.forEach(button => {
        button.addEventListener("click", () => {
            tabButtons.forEach(btn => btn.classList.remove("active"));
            button.classList.add("active");

            tabPanels.forEach(panel => panel.classList.remove("active"));

            const targetTab = button.getAttribute("data-tab");
            document.getElementById(targetTab).classList.add("active");

            handleTabVisibility(targetTab, searchContainer, mainContent, paragraphContainer, pagination);
        });
    });
}

// タブに基づいて表示内容を切り替え
function handleTabVisibility(targetTab, searchContainer, mainContent, paragraphContainer, pagination) {
    if (targetTab === "tab2") {
        searchContainer.classList.add("hidden");
        mainContent.classList.add("full-width");
        paragraphContainer.style.display = "block";
        pagination.style.display = "none";
    } else {
        searchContainer.classList.remove("hidden");
        mainContent.classList.remove("full-width");
        paragraphContainer.style.display = "none";
        pagination.style.display = "block";
    }
}

// フォームの初期化処理
function setupSearchHandler() {
    document.getElementById('feedbackForm').addEventListener('submit', function(event) {
        event.preventDefault();
        const formData = {
            name: document.getElementById('name').value,
            email: document.getElementById('email').value,
            category: document.getElementById('category').value,
            message: document.getElementById('message').value
        };

        submitFeedback(formData);
    });
}

// フィードバック送信処理
function submitFeedback(formData) {
    fetch('/submit-feedback', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(formData)
    })
    .then(response => {
        if (response.ok) {
            document.getElementById('responseMessage').classList.remove('hidden');
            document.getElementById('feedbackForm').reset();
        } else {
            alert('送信に失敗しました。もう一度お試しください。');
        }
    })
    .catch(error => console.error('エラー:', error));
}
