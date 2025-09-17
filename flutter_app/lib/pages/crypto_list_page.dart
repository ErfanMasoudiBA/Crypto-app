import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;
import '../models/crypto_coin.dart';
import '../services/crypto_api.dart';

class CryptoListPage extends StatefulWidget {
  const CryptoListPage({super.key});

  @override
  State<CryptoListPage> createState() => _CryptoListPageState();
}

class _CryptoListPageState extends State<CryptoListPage> {
  List<CryptoCoin> _cryptos = [];
  bool _isLoading = false;
  String? _errorMessage;
  int _currentPage = 1;
  int _totalPages = 1;
  bool _hasNext = false;
  bool _hasPrev = false;
  String _lastUpdated = '';
  final ScrollController _scrollController = ScrollController();
  bool _isAppending = false;

  @override
  void initState() {
    super.initState();
    _loadCryptos();
    _scrollController.addListener(_onScroll);
  }

  Future<void> _loadCryptos({int page = 1}) async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      print('CryptoListPage: Starting to load cryptos page $page...');
      
      // First test basic connectivity
      print('CryptoListPage: Testing basic connectivity...');
      final testResponse = await http.get(
        Uri.parse('${CryptoApi.baseUrl}/'),
      ).timeout(const Duration(seconds: 10));
      
      if (testResponse.statusCode == 200) {
        print('CryptoListPage: Basic connectivity OK');
      } else {
        throw Exception('Basic connectivity test failed: ${testResponse.statusCode}');
      }
      
      // Fetch paginated cryptos
      final cryptoResponse = await CryptoApi.fetchCryptos(page: page, perPage: 10);
      print('CryptoListPage: Successfully loaded ${cryptoResponse.coins.length} cryptos on page ${cryptoResponse.page}');
      
      setState(() {
        if (page == 1 || !_isAppending) {
          _cryptos = cryptoResponse.coins;
        } else {
          _cryptos = [..._cryptos, ...cryptoResponse.coins];
        }
        _currentPage = cryptoResponse.page;
        _totalPages = cryptoResponse.totalPages;
        _hasNext = cryptoResponse.hasNext;
        _hasPrev = cryptoResponse.hasPrev;
        _lastUpdated = cryptoResponse.lastUpdated;
        _isLoading = false;
        _isAppending = false;
      });
    } catch (e) {
      print('CryptoListPage: Error loading cryptos: $e');
      setState(() {
        _errorMessage = e.toString();
        _isLoading = false;
      });
    }
  }

  void _onScroll() {
    if (_scrollController.position.pixels >= _scrollController.position.maxScrollExtent - 200) {
      if (_hasNext && !_isLoading && !_isAppending) {
        _isAppending = true;
        _goToNextPage();
      }
    }
  }

  Future<void> _testConnectivity() async {
    try {
      print('Testing connectivity to API...');
      final response = await http.get(
        Uri.parse('${CryptoApi.baseUrl}/'),
      ).timeout(const Duration(seconds: 10));
      
      if (response.statusCode == 200) {
        print('Connectivity test successful!');
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ API connectivity test successful!'),
            backgroundColor: Colors.green,
          ),
        );
      } else {
        print('Connectivity test failed: ${response.statusCode}');
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('❌ API connectivity test failed: ${response.statusCode}'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } catch (e) {
      print('Connectivity test error: $e');
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: Text('❌ API connectivity test error: $e'),
          backgroundColor: Colors.red,
        ),
      );
    }
  }

  Future<void> _goToNextPage() async {
    if (_hasNext && !_isLoading) {
      await _loadCryptos(page: _currentPage + 1);
    }
  }

  Future<void> _goToPreviousPage() async {
    if (_hasPrev && !_isLoading) {
      await _loadCryptos(page: _currentPage - 1);
    }
  }

  Future<void> _refreshCurrentPage() async {
    await _loadCryptos(page: _currentPage);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Cryptocurrencies'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        actions: [
          IconButton(
            icon: const Icon(Icons.bug_report),
            onPressed: _testConnectivity,
            tooltip: 'Test Connectivity',
          ),
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _refreshCurrentPage,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(),
            SizedBox(height: 16),
            Text('Loading cryptocurrencies...'),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.error_outline,
                size: 64,
                color: Colors.red[300],
              ),
              const SizedBox(height: 16),
              Text(
                'Failed to load cryptocurrencies',
                style: Theme.of(context).textTheme.headlineSmall,
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 8),
              Text(
                _errorMessage!,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 24),
              ElevatedButton.icon(
                onPressed: _loadCryptos,
                icon: const Icon(Icons.refresh),
                label: const Text('Retry'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 12),
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (_cryptos.isEmpty) {
      return const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.inbox_outlined,
              size: 64,
              color: Colors.grey,
            ),
            SizedBox(height: 16),
            Text(
              'No cryptocurrencies found',
              style: TextStyle(fontSize: 18, color: Colors.grey),
            ),
          ],
        ),
      );
    }

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.all(16.0),
          child: Column(
            children: [
              Row(
                children: [
                  Text(
                    'Page $_currentPage of $_totalPages',
                    style: Theme.of(context).textTheme.titleMedium?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                  const Spacer(),
                  Text(
                    'Last updated: ${_getLastUpdated()}',
                    style: Theme.of(context).textTheme.bodySmall?.copyWith(
                      color: Colors.grey[500],
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Row(
                children: [
                  Text(
                    'Showing ${_cryptos.length} cryptocurrencies',
                    style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
        Expanded(
          child: ListView.separated(
            controller: _scrollController,
            itemCount: _cryptos.length,
            separatorBuilder: (context, index) => const Divider(height: 1),
            itemBuilder: (context, index) {
              final crypto = _cryptos[index];
              return _buildCryptoItem(crypto);
            },
          ),
        ),
        _buildPaginationControls(),
      ],
    );
  }

  Widget _buildPaginationControls() {
    return Container(
      padding: const EdgeInsets.all(16.0),
      decoration: BoxDecoration(
        color: Theme.of(context).colorScheme.surface,
        border: Border(
          top: BorderSide(
            color: Colors.grey[300]!,
            width: 1,
          ),
        ),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          ElevatedButton.icon(
            onPressed: _hasPrev && !_isLoading ? _goToPreviousPage : null,
            icon: const Icon(Icons.chevron_left),
            label: const Text('Previous'),
            style: ElevatedButton.styleFrom(
              backgroundColor: _hasPrev && !_isLoading 
                  ? Theme.of(context).colorScheme.primary
                  : Colors.grey[300],
              foregroundColor: _hasPrev && !_isLoading 
                  ? Colors.white
                  : Colors.grey[600],
            ),
          ),
          Text(
            'Page $_currentPage of $_totalPages',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              fontWeight: FontWeight.w500,
            ),
          ),
          ElevatedButton.icon(
            onPressed: _hasNext && !_isLoading ? _goToNextPage : null,
            icon: const Icon(Icons.chevron_right),
            label: const Text('Next'),
            style: ElevatedButton.styleFrom(
              backgroundColor: _hasNext && !_isLoading 
                  ? Theme.of(context).colorScheme.primary
                  : Colors.grey[300],
              foregroundColor: _hasNext && !_isLoading 
                  ? Colors.white
                  : Colors.grey[600],
            ),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _scrollController.dispose();
    super.dispose();
  }

  Widget _buildCryptoItem(CryptoCoin crypto) {
    return ListTile(
      contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
      leading: _buildLeading(crypto),
      title: Row(
        children: [
          Expanded(
            child: Text(
              crypto.name,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 16,
              ),
              overflow: TextOverflow.ellipsis,
            ),
          ),
          const SizedBox(width: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
            decoration: BoxDecoration(
              color: Colors.grey[200],
              borderRadius: BorderRadius.circular(12),
            ),
            child: Text(
              crypto.symbol,
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 12,
                color: Colors.black87,
              ),
            ),
          ),
        ],
      ),
      subtitle: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const SizedBox(height: 4),
          Row(
            children: [
              Text(
                'Price: ${crypto.formattedPrice}',
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(width: 16),
              if (crypto.change24hPct != null) ...[
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                  decoration: BoxDecoration(
                    color: crypto.changeColor.withOpacity(0.1),
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    crypto.formattedChange24h,
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: crypto.changeColor,
                    ),
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 2),
          Text(
            'Market Cap: ${crypto.formattedMarketCap}',
            style: TextStyle(
              fontSize: 12,
              color: Colors.grey[600],
            ),
          ),
        ],
      ),
      onTap: () => _showCryptoDetails(crypto),
    );
  }

  Widget _buildLeading(CryptoCoin crypto) {
    if (crypto.imageUrl != null && crypto.imageUrl!.isNotEmpty) {
      return ClipRRect(
        borderRadius: BorderRadius.circular(16),
        child: Image.network(
          crypto.imageUrl!,
          width: 32,
          height: 32,
          fit: BoxFit.cover,
          errorBuilder: (context, _, __) => _buildRankBadge(crypto.rank),
          loadingBuilder: (context, child, loadingProgress) {
            if (loadingProgress == null) return child;
            return _buildRankBadge(crypto.rank);
          },
        ),
      );
    }
    return _buildRankBadge(crypto.rank);
  }

  Widget _buildRankBadge(int? rank) {
    if (rank == null) {
      return Container(
        width: 32,
        height: 32,
        decoration: BoxDecoration(
          color: Colors.grey[300],
          shape: BoxShape.circle,
        ),
        child: const Icon(
          Icons.help_outline,
          size: 16,
          color: Colors.grey,
        ),
      );
    }

    Color badgeColor;
    if (rank <= 10) {
      badgeColor = Colors.amber[600]!;
    } else if (rank <= 50) {
      badgeColor = Colors.blue[600]!;
    } else if (rank <= 100) {
      badgeColor = Colors.green[600]!;
    } else {
      badgeColor = Colors.grey[600]!;
    }

    return Container(
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        color: badgeColor,
        shape: BoxShape.circle,
      ),
      child: Center(
        child: Text(
          rank.toString(),
          style: const TextStyle(
            color: Colors.white,
            fontWeight: FontWeight.bold,
            fontSize: 12,
          ),
        ),
      ),
    );
  }

  String _getLastUpdated() {
    if (_lastUpdated.isEmpty) return 'N/A';
    
    try {
      final dateTime = DateTime.parse(_lastUpdated);
      final now = DateTime.now();
      final difference = now.difference(dateTime);
      
      if (difference.inMinutes < 1) {
        return 'Just now';
      } else if (difference.inMinutes < 60) {
        return '${difference.inMinutes}m ago';
      } else if (difference.inHours < 24) {
        return '${difference.inHours}h ago';
      } else {
        return '${difference.inDays}d ago';
      }
    } catch (e) {
      return 'Unknown';
    }
  }

  void _showCryptoDetails(CryptoCoin crypto) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: Row(
          children: [
            _buildRankBadge(crypto.rank),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    crypto.name,
                    style: const TextStyle(fontSize: 18),
                  ),
                  Text(
                    crypto.symbol,
                    style: TextStyle(
                      fontSize: 14,
                      color: Colors.grey[600],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildDetailRow('Price', crypto.formattedPrice),
            _buildDetailRow('Market Cap', crypto.formattedMarketCap),
            _buildDetailRow('24h Change', crypto.formattedChange24h),
            if (crypto.totalVolumeUsd != null)
              _buildDetailRow('24h Volume', _formatVolume(crypto.totalVolumeUsd!)),
            _buildDetailRow('Last Updated', _formatLastUpdated(crypto.lastUpdated)),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            label,
            style: const TextStyle(fontWeight: FontWeight.w500),
          ),
          Text(value),
        ],
      ),
    );
  }

  String _formatVolume(double volume) {
    if (volume >= 1e12) {
      return '\$${(volume / 1e12).toStringAsFixed(2)}T';
    } else if (volume >= 1e9) {
      return '\$${(volume / 1e9).toStringAsFixed(2)}B';
    } else if (volume >= 1e6) {
      return '\$${(volume / 1e6).toStringAsFixed(2)}M';
    } else if (volume >= 1e3) {
      return '\$${(volume / 1e3).toStringAsFixed(2)}K';
    } else {
      return '\$${volume.toStringAsFixed(2)}';
    }
  }

  String _formatLastUpdated(String? lastUpdated) {
    if (lastUpdated == null) return 'N/A';
    
    try {
      final dateTime = DateTime.parse(lastUpdated);
      return '${dateTime.day}/${dateTime.month}/${dateTime.year} ${dateTime.hour}:${dateTime.minute.toString().padLeft(2, '0')}';
    } catch (e) {
      return 'Invalid date';
    }
  }
}
