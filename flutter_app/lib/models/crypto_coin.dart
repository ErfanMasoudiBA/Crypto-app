import 'package:flutter/material.dart';

class CryptoCoin {
  final int? rank;
  final String symbol;
  final String id;
  final String name;
  final double? priceUsd;
  final double? marketCapUsd;
  final double? change24hPct;
  final double? totalVolumeUsd;
  final String? lastUpdated;
  final String? imageUrl;

  CryptoCoin({
    this.rank,
    required this.symbol,
    required this.id,
    required this.name,
    this.priceUsd,
    this.marketCapUsd,
    this.change24hPct,
    this.totalVolumeUsd,
    this.lastUpdated,
    this.imageUrl,
  });

  factory CryptoCoin.fromJson(Map<String, dynamic> json) {
    try {
      print('CryptoCoin: Parsing JSON: ${json.keys.toList()}');
      return CryptoCoin(
        rank: json['rank'],
        symbol: json['symbol'] ?? '',
        id: json['id'] ?? '',
        name: json['name'] ?? '',
        priceUsd: json['price_usd']?.toDouble(),
        marketCapUsd: json['market_cap_usd']?.toDouble(),
        change24hPct: json['change_24h_pct']?.toDouble(),
        totalVolumeUsd: json['total_volume_usd']?.toDouble(),
        lastUpdated: json['last_updated'],
        imageUrl: json['image_url'],
      );
    } catch (e) {
      print('CryptoCoin: Error parsing JSON: $e');
      print('CryptoCoin: JSON data: $json');
      rethrow;
    }
  }

  Map<String, dynamic> toJson() {
    return {
      'rank': rank,
      'symbol': symbol,
      'id': id,
      'name': name,
      'price_usd': priceUsd,
      'market_cap_usd': marketCapUsd,
      'change_24h_pct': change24hPct,
      'total_volume_usd': totalVolumeUsd,
      'last_updated': lastUpdated,
      'image_url': imageUrl,
    };
  }

  String get formattedPrice {
    if (priceUsd == null) return 'N/A';
    if (priceUsd! < 0.01) {
      return '\$${priceUsd!.toStringAsFixed(6)}';
    } else if (priceUsd! < 1) {
      return '\$${priceUsd!.toStringAsFixed(4)}';
    } else {
      return '\$${priceUsd!.toStringAsFixed(2)}';
    }
  }

  String get formattedMarketCap {
    if (marketCapUsd == null) return 'N/A';
    if (marketCapUsd! >= 1e12) {
      return '\$${(marketCapUsd! / 1e12).toStringAsFixed(2)}T';
    } else if (marketCapUsd! >= 1e9) {
      return '\$${(marketCapUsd! / 1e9).toStringAsFixed(2)}B';
    } else if (marketCapUsd! >= 1e6) {
      return '\$${(marketCapUsd! / 1e6).toStringAsFixed(2)}M';
    } else if (marketCapUsd! >= 1e3) {
      return '\$${(marketCapUsd! / 1e3).toStringAsFixed(2)}K';
    } else {
      return '\$${marketCapUsd!.toStringAsFixed(2)}';
    }
  }

  String get formattedChange24h {
    if (change24hPct == null) return 'N/A';
    final change = change24hPct!;
    final sign = change >= 0 ? '+' : '';
    return '$sign${change.toStringAsFixed(2)}%';
  }

  Color get changeColor {
    if (change24hPct == null) return Colors.grey;
    return change24hPct! >= 0 ? Colors.green : Colors.red;
  }
}
